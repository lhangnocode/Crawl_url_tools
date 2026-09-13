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


GENERIC_DEEP_INTERACTION_PROMPT = """
You are a web application security discovery expert. Your goal is to explore
the target web platform to reveal as many distinct endpoints, routes, and
interaction points as possible (GET navigation links and POST/PUT/DELETE actions).

Priority execution order:
1. AUTHENTICATION (MANDATORY FIRST STEP):
   Navigate directly to the login page (e.g., /user or login button). Log in using
   the provided administrative credentials:
   - Username: admin
   - Password: admin123
   Submit the login form and ensure you are fully authenticated.

2. USER & ADMIN MENU DISCOVERY:
   Once logged in, click on the user profile/avatar/menu dropdown (usually in the
   top-right corner or sidebar) to expand dynamic items. Open and visit each link
   inside it once (e.g., My Channel, My Account, Upload Video, Configurations/Site Settings,
   Plugins, User Groups, Subscriptions, History).

3. STATE-CHANGING ACTIONS & FORMS:
   Perform realistic interactions to trigger hidden POST/AJAX endpoints:
   - Open the Video Upload modal or page, inspect the form, and attempt to submit
     minimal valid text/metadata (title, category) without breaking.
   - Use the Search form: submit a test query (e.g., 'test video').
   - Open a channel, video manager, or category page and visit sub-tabs.
   - Open the Contact, About, or Help pages.

4. REMAINING NAVIGATION:
   Click through remaining header, footer, and sidebar links, pagination controls,
   and filter buttons (e.g., /trending, /audioOnly, /videoOnly).

OUTPUT REQUIREMENTS:
For every step, capture and record the visited URL/route (including paths,
query parameters, and dynamic route segments). Return ALL unique URLs observed
throughout the entire session alongside a summary of the actions taken.

Only act on this authorized test target. Use safe, realistic test data without attack payloads.
"""

# Minimal prompt used only to sanity-check that the agent endpoint itself works.
SANITY_CHECK_PROMPT = """
Navigate to the target site and list the first 5 links or routes you observe on the page. Do not click anything else.
"""


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
    print("\n🧪 [SANITY CHECK] Chạy thử agent với tác vụ tối giản trước...")
    job_id = start_agent_job(session, target_url, SANITY_CHECK_PROMPT, DiscoveredLinks.model_json_schema())
    if not job_id:
        print("🚨 Ngay cả tác vụ tối giản cũng không lấy được job id -> vấn đề ở API/tài khoản, không phải prompt.")
        return False

    result = poll_agent_job(session, job_id, max_wait_seconds=max_wait_seconds, poll_interval=10)
    if result and result.get("status") == "completed":
        data = result.get("data") or {}
        links = data.get("links", []) or []
        print(f"✅ Sanity check PASS — {len(links)} link tìm được: {links}")
        # Kiểm tra thêm: nếu link toàn thuộc domain ngrok chính nó (interstitial),
        # cảnh báo ngay để không mất thời gian chạy prompt phức tạp vô ích.
        if links and all("ngrok" in l.lower() or l.startswith("#") for l in links):
            print("⚠️ Các link tìm được có vẻ vẫn thuộc trang chặn ngrok, không phải app thật. "
                  "Kiểm tra lại bước 'Visit Site' trong prompt hoặc đổi sang Cloudflare Tunnel.")
        return True

    print("🚨 Sanity check KHÔNG hoàn tất -> nghi ngờ cao vấn đề nằm ở API/tài khoản "
          f"(model 'spark-1-pro' hoặc tính năng agent), báo Firecrawl support kèm job id: {job_id}")
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
                (".png", ".jpg", ".jpeg", ".svg", ".css", ".js", ".woff2", ".ico", ".mp4", ".webm")
            ):
                unique_endpoints.add(f"{method.upper()} - {uri.split('?')[0]}")

        return sorted(unique_endpoints)

    except Exception as e:
        print(f"🚨 Ngrok error: {e!s}")
        return []


# --- MAIN PIPELINE ---
if __name__ == "__main__":
    TARGET_URL = "https://possibilities-spider-flying-tenant.trycloudflare.com/"
    session = _make_retrying_session()

    # Bước 0: chạy sanity check trước tiên — QUAN TRỌNG với target mới, vì
    # cần xác nhận agent thực sự vượt qua được trang chặn ngrok trước khi
    # chạy prompt phức tạp (tốn nhiều thời gian hơn nếu thất bại lặp lại).
    if not sanity_check_agent(session, TARGET_URL):
        print("⛔ Dừng lại: cần xử lý vấn đề API/tài khoản/ngrok trước khi thử prompt phức tạp hơn.")
        exit()

    print("\n[PHASE 1] 🤖 Launching AI Agent (manual poll, real-time progress)...")
    job_id = start_agent_job(session, TARGET_URL, GENERIC_DEEP_INTERACTION_PROMPT,
                              DiscoveredLinks.model_json_schema())

    ui_links: list[str] = []
    if job_id:
        result_json = poll_agent_job(session, job_id, max_wait_seconds=1200, poll_interval=10)
        if result_json and result_json.get("status") == "completed":
            data = result_json.get("data") or {}
            ui_links = sorted(set(data.get("links", []) or []))
            actions = data.get("actions_taken", []) or []
            print(f"✅ Agent finished. Actions taken: {', '.join(actions)}")
        else:
            print("⚠️ Agent job không hoàn tất trong thời gian chờ. "
                  f"Job id để tra cứu/hủy trên dashboard Firecrawl: {job_id}")
    else:
        print("❌ Không tạo được agent job (không có job id trong response).")

    # backend_endpoints = extract_ngrok_endpoints()
    backend_endpoints = []  

    if ui_links:
        with open("avideo_agent_ui(V5).txt", "w", encoding="utf-8") as f:
            f.writelines(f"{url}\n" for url in ui_links)
        print(f"📂 Saved {len(ui_links)} UI links to: avideo_agent_ui(V5).txt")

    if backend_endpoints:
        with open("avideo_ngrok_backend_endpoints(V5).txt", "w", encoding="utf-8") as f:
            f.writelines(f"{ep}\n" for ep in backend_endpoints)
        print(f"📂 Saved {len(backend_endpoints)} server endpoints to: avideo_ngrok_backend_endpoints(V5).txt")