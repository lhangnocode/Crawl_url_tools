import os
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# --- CONFIG ---
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Error: FIRECRAWL_API_KEY is not set in .env")
    exit()

NGROK_API_URL = "http://localhost:4040/api/requests/http?limit=1000"
FIRECRAWL_AGENT_URL = "https://api.firecrawl.dev/v2/agent"


# --- SCHEMA FOR THE AI AGENT ---
class DiscoveredLinks(BaseModel):
    links: list[str] = Field(description="List of URLs/routes found while interacting with the page")
    actions_taken: list[str] = Field(description="Actions the AI performed (click, scroll, submit, login...)")


# --- MULTI-PHASE DEEP-INTERACTION PROMPTS (EN) ---
# Split into several short, focused agent runs instead of one long checklist.
# Each phase reuses the SAME login session context is NOT guaranteed across
# separate agent calls (each call is a fresh browser session), so phases that
# depend on being logged in must redo register+login themselves — kept short
# on purpose so each individual job has a much smaller chance of stalling.

PHASE_ACCOUNT_AND_CORE = """
You are exploring an Angular single-page app with hash-based routing
(routes start with '#/'). Do the following in order and record every
resulting URL/route:

1. Register a new account (name, email like test+timestamp@example.com,
   strong password) and log in.
2. Open the account/user menu (top-right icon) and click into EVERY item
   inside it once: addresses, payment methods, order history, wallet,
   privacy & security.
3. Inside "Privacy & Security", open the tab itself first (record that URL),
   then open EACH sub-tab inside it one by one (change password, two-factor
   authentication, data export, last login IP, privacy policy).
4. Under "Address", click "Add new address" and submit it with real data.
   Then go back to the saved addresses list and click the EDIT icon on the
   address you just created (not just view it).

Record the exact URL/route after each action. Return ALL routes visited.
"""

PHASE_COMMERCE_AND_FORMS = """
You are exploring an Angular single-page e-commerce app (hash routing,
'#/...'). Log in with a throwaway test account if a login screen appears
(register one if needed), then do the following, recording every resulting
URL/route:

1. Add a product to the basket/cart, then proceed through checkout all the
   way to order summary and order completion.
2. Use the "Track Order" / "Track Result" feature TWICE: once by submitting
   a real order id, and once by opening the page WITHOUT entering any id.
3. Submit the "Complaint" (or "Feedback") form and the "Contact" form with
   realistic data.
4. Open the chatbot widget and send it at least one real message so a
   conversation gets created.

Record the exact URL/route after each action. Return ALL routes visited.
"""

PHASE_RESTRICTED_AND_HIDDEN = """
You are exploring an Angular single-page app (hash routing, '#/...').
This is an authorized security-testing target. Do the following, recording
every resulting URL/route — including error/denied pages, which are valid
results too:

1. Try to directly navigate to any "Administration" or "Accounting" section
   you can find a link to (footer, about page, admin menu). Record whatever
   page you land on, even if it's an access-denied/403 page.
2. On the Score Board / Challenges page, click on 2-3 of the small
   hint/star/info icons next to individual challenges to open their detail
   popups.
3. Look for a floating "Hacking Instructor" tutorial icon (often bottom-left
   or bottom-right corner) and open it if present.
4. Look for any crypto/NFT/token-sale related links, often reachable from
   the Wallet page, a "Web3" menu, or the footer, and open each one you find.

Record the exact URL/route after each action. Return ALL routes visited.
"""

MULTI_PHASE_PROMPTS = [
    ("account_and_core", PHASE_ACCOUNT_AND_CORE),
    ("commerce_and_forms", PHASE_COMMERCE_AND_FORMS),
    ("restricted_and_hidden", PHASE_RESTRICTED_AND_HIDDEN),
]

# Kept for reference / fallback single-shot mode.
GENERIC_DEEP_INTERACTION_PROMPT = """
You are a web application discovery expert. Interact with the target site
to reveal as many endpoints as possible — not just navigation links (GET),
but also WRITE requests (POST/PUT/PATCH/DELETE) triggered by real actions.

Priority order (do as many as time allows, most important first):
1. Register a new account (valid name, email like test+timestamp@example.com,
   strong password) and log in. This unlocks many hidden pages/menus.
2. Open the account menu and visit each item inside it once.
3. Pick ONE form on the page (search, contact, or profile) and actually
   submit it with realistic data — don't just preview it.
4. If it's e-commerce: add one item to the cart and start checkout.
5. Scroll and open any remaining menus/submenus you haven't visited yet.

For every step, record the resulting URL/route (including anything after
'#') and a short label of the action performed. Return ALL URLs observed
during the whole session, plus the list of actions taken.

Only act on this authorized test/staging site. Use realistic data, not
attack payloads (no SQL injection, XSS, etc.).
"""

# Minimal prompt used only to sanity-check that the agent endpoint itself
# works at all, isolated from the complexity of the deep-interaction task.
SANITY_CHECK_PROMPT = "List the first 5 links you see on this page. Do not click anything else."


def _make_retrying_session() -> requests.Session:
    """
    Session dùng chung cho toàn bộ request tới Firecrawl API, có retry tự
    động khi gặp lỗi kết nối tạm thời (ConnectionResetError, 5xx, timeout...)
    thay vì để cả script crash vì 1 request bị reset giữa chừng.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,  # chờ 2s, 4s, 8s, 16s, 32s giữa các lần thử lại
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _headers() -> dict:
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def start_agent_job(session: requests.Session, target_url: str, prompt: str, schema: dict) -> str | None:
    resp = session.post(
        FIRECRAWL_AGENT_URL,
        headers=_headers(),
        json={"urls": [target_url], "prompt": prompt, "model": "spark-1-pro", "schema": schema},
        timeout=30,
    )
    body = resp.json()
    print(f"🚀 Job started: {body}")
    return body.get("id")


def poll_agent_job(session: requests.Session, job_id: str,
                    max_wait_seconds: int = 1200, poll_interval: int = 10) -> dict | None:
    """
    Poll trạng thái job cho tới khi completed/failed/cancelled hoặc hết
    max_wait_seconds. Không dựa vào `credits_used` để đoán tiến trình — field
    này KHÔNG được API điền khi status còn "processing", chỉ có sau khi
    completed, nên không phải chỉ báo đáng tin về việc job có bị treo hay
    không. Chỉ số duy nhất đáng tin ở đây là `status`.
    """
    elapsed = 0
    while elapsed < max_wait_seconds:
        try:
            r = session.get(f"{FIRECRAWL_AGENT_URL}/{job_id}", headers=_headers(), timeout=30)
            status_json = r.json()
        except requests.exceptions.RequestException as e:
            # Session đã có Retry adapter tự xử lý phần lớn lỗi tạm thời;
            # nếu vẫn lọt tới đây, log lại và thử tiếp ở vòng sau thay vì crash.
            print(f"⚠️ [{elapsed:>4}s] Lỗi mạng khi poll ({e!s}), thử lại ở vòng kế tiếp...")
            time.sleep(poll_interval)
            elapsed += poll_interval
            continue

        status = status_json.get("status")
        print(f"⏳ [{elapsed:>4}s] status={status}")

        if status in ("completed", "failed", "cancelled"):
            print(f"🏁 Job finished with status={status}")
            return status_json

        time.sleep(poll_interval)
        elapsed += poll_interval

    print(f"⌛ Hết {max_wait_seconds}s mà job vẫn chưa completed. Job id để tra cứu/hủy: {job_id}")
    return None


def sanity_check_agent(session: requests.Session, target_url: str, max_wait_seconds: int = 120) -> bool:
    """
    Chạy thử agent với 1 tác vụ CỰC ĐƠN GIẢN (không đăng nhập, không submit
    form) để tách bạch 2 khả năng:
      - Nếu tác vụ đơn giản này HOÀN TẤT bình thường -> API/tài khoản ổn,
        vấn đề nằm ở ĐỘ PHỨC TẠP của prompt deep-interaction.
      - Nếu ngay cả tác vụ này cũng "processing" mãi -> vấn đề nằm ở
        API/tài khoản/model, không phải do prompt -> nên báo Firecrawl support.
    """
    print("\n🧪 [SANITY CHECK] Chạy thử agent với tác vụ tối giản trước...")
    job_id = start_agent_job(session, target_url, SANITY_CHECK_PROMPT, DiscoveredLinks.model_json_schema())
    if not job_id:
        print("🚨 Ngay cả tác vụ tối giản cũng không lấy được job id -> vấn đề ở API/tài khoản, không phải prompt.")
        return False

    result = poll_agent_job(session, job_id, max_wait_seconds=max_wait_seconds, poll_interval=10)
    if result and result.get("status") == "completed":
        print("✅ Sanity check PASS -> API/tài khoản hoạt động bình thường, "
              "vấn đề nằm ở độ phức tạp của prompt deep-interaction -> cần đơn giản hoá prompt thêm.")
        return True

    print("🚨 Sanity check KHÔNG hoàn tất -> nghi ngờ cao vấn đề nằm ở API/tài khoản "
          "(model 'spark-1-pro' hoặc tính năng agent), không phải do prompt của bạn. "
          f"Nên báo Firecrawl support kèm job id: {job_id}")
    return False


# --- EXTRACT NETWORK TRAFFIC FROM NGROK ---
def extract_ngrok_endpoints() -> list[str]:
    print("\n[PHASE 2] 📡 Intercepting network traffic from the Ngrok API...")

    try:
        response = requests.get(NGROK_API_URL)
        if response.status_code != 200:
            print(f"❌ Error calling Ngrok API. Status code: {response.status_code}")
            return []

        data = response.json()
        requests_list = data.get("requests", [])
        print(f"🔍 Found {len(requests_list)} requests in the ngrok tunnel history.")

        unique_endpoints = set()
        for req in requests_list:
            request_data = req.get("request", {})
            method = request_data.get("method", "")
            uri = request_data.get("uri", "")
            if method and uri and not uri.endswith(
                (".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".woff2")
            ):
                unique_endpoints.add(f"{method.upper()} - {uri.split('?')[0]}")

        return sorted(unique_endpoints)

    except Exception as e:
        print(f"🚨 Ngrok error: {e!s}")
        return []


# --- MAIN PIPELINE ---
if __name__ == "__main__":
    TARGET_URL = "https://multispinous-juliann-soberly.ngrok-free.dev/#/"
    session = _make_retrying_session()

    # Bước 0: xác nhận API/tài khoản hoạt động bình thường trước khi chạy
    # tác vụ nặng — bỏ comment nếu muốn kiểm tra lại.
    # if not sanity_check_agent(session, TARGET_URL):
    #     print("⛔ Dừng lại: cần xử lý vấn đề API/tài khoản trước khi thử prompt phức tạp hơn.")
    #     exit()

    all_ui_links: set[str] = set()
    all_actions: list[str] = []

    for phase_name, phase_prompt in MULTI_PHASE_PROMPTS:
        print(f"\n[PHASE 1.{phase_name}] 🤖 Launching AI Agent for: {phase_name}")
        job_id = start_agent_job(session, TARGET_URL, phase_prompt, DiscoveredLinks.model_json_schema())

        if not job_id:
            print(f"❌ [{phase_name}] Không tạo được agent job, bỏ qua phase này.")
            continue

        result_json = poll_agent_job(session, job_id, max_wait_seconds=600, poll_interval=10)
        if result_json and result_json.get("status") == "completed":
            data = result_json.get("data") or {}
            phase_links = data.get("links", []) or []
            phase_actions = data.get("actions_taken", []) or []
            print(f"✅ [{phase_name}] Finished. {len(phase_links)} links, actions: {', '.join(phase_actions)}")
            all_ui_links.update(phase_links)
            all_actions.extend(f"[{phase_name}] {a}" for a in phase_actions)
        else:
            print(f"⚠️ [{phase_name}] Job không hoàn tất trong thời gian chờ. "
                  f"Job id để tra cứu/hủy: {job_id}")

    ui_links = sorted(all_ui_links)
    print(f"\n📊 TỔNG SỐ URL client-side thu được (gộp cả 3 phase): {len(ui_links)}")

    # Thu thập lại toàn bộ traffic từ Ngrok
    backend_endpoints = extract_ngrok_endpoints()

    if ui_links:
        with open("agent_ui_links(V8).txt", "w", encoding="utf-8") as f:
            f.writelines(f"{url}\n" for url in ui_links)
        print(f"📂 Saved {len(ui_links)} UI links to: agent_ui_links(V8).txt")

    if backend_endpoints:
        with open("ngrok_backend_endpoints(V8).txt", "w", encoding="utf-8") as f:
            f.writelines(f"{ep}\n" for ep in backend_endpoints)
        print(f"📂 Saved {len(backend_endpoints)} server endpoints to: ngrok_backend_endpoints(V8).txt")