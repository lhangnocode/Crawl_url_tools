import asyncio
import csv
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from browser_use import Agent, Browser, BrowserProfile, ChatOpenAI
from browser_use.browser import ProxySettings
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Cấu hình
# ---------------------------------------------------------------------------
TARGET_URL = "http://192.168.1.25:3001/#/"
TARGET_HOST = urlparse(TARGET_URL).hostname  # -> "192.168.1.25"

ZAP_PROXY = "http://localhost:8080"
ZAP_API_URL = "http://localhost:8080"
ZAP_API_KEY = os.getenv("ZAP_API_KEY", "")

OUTPUT_DIR = Path("crawl_output")
OUTPUT_DIR.mkdir(exist_ok=True)
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")

MAX_STEPS = 100

llm = ChatOpenAI(
    model=os.getenv("NARAROUTER_MODEL", "mistral-medium-3-5"),
    api_key=os.getenv("NARAROUTER_API_KEY"),
    base_url=os.getenv("NARAROUTER_BASE_URL"),
)

extend_system_message = """
You are an aggressive QA Automation Tester.
Your goal is to maximize 'Code Coverage' within the target application ONLY.
- Do not follow a happy path. Try to click elements you haven't clicked before.
- Do NOT attempt real external OAuth logins (e.g. "Login with Google") - these are
  decoys in this application and will take you outside the target domain.
- If you see a Login form, use credentials: prodz18022005@gmail.com / Dinhkhang18022005 to access internal features.
- Avoid clicking 'Logout' unless you have explored everything else.

RULES FOR NAVIGATION:
1. If a link opens in the SAME tab and leads to an error or dead end, use 'go_back'.
   Do NOT use 'close_tab' unless a NEW tab was explicitly opened (target="_blank").
2. Never navigate outside the target host.
"""

task = f"""
Go to {TARGET_URL}.
Explore the application deeply by finding and clicking all interactive elements. 
Map out the structure of the site by visiting every accessible URL.
Stay strictly within the {TARGET_HOST} domain.
"""

initial_action = [
    {"go_to_url": {"url": TARGET_URL, "new_tab": False}},
    {"wait": {"seconds": 1}},
]

browser = Browser(
    browser_profile=BrowserProfile(
        # Giữ proxy để ZAP bắt toàn bộ traffic thật (đây là nguồn dữ liệu chính)
        proxy=ProxySettings(server=ZAP_PROXY),
        # Giới hạn agent chỉ ở trong target -> tránh dữ liệu bị nhiễu domain lạ
        allowed_domains=[TARGET_HOST, f"*.{TARGET_HOST}"],
        # Không cần disable_security / disable-web-security: proxy đã bắt hết
        # traffic ở tầng network rồi, không phụ thuộc CORS/same-origin của browser.
        ignore_https_errors=True,  # phòng khi deploy bản HTTPS sau này
        args=[
            "--ignore-certificate-errors",
            "--disable-gpu",
        ],
        # Các field context được đưa thẳng vào BrowserProfile (API hiện tại đã flatten,
        # không còn dùng new_context_config lồng nhau như bản cũ)
        user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 720},
        permissions=["geolocation", "notifications"],
    )
)


def export_agent_log(result, path: Path):
    """Xuất URL mà agent CHỦ ĐỘNG điều hướng tới (navigation-level, không bắt được
    XHR/fetch ngầm)."""
    urls = sorted(set(result.urls()))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(urls, f, indent=2, ensure_ascii=False)
    print(f"[agent-log] {len(urls)} URL -> {path}")
    return urls


def export_zap_sitemap(path_json: Path, path_csv: Path):
    """Xuất toàn bộ URL mà ZAP thấy được qua proxy (traffic thật, bao gồm API call ẩn)."""
    try:
        from zapv2 import ZAPv2
    except ImportError:
        print(
            "[zap] Chưa cài python-owasp-zap-v2.4, bỏ qua export tự động. "
            "Bạn có thể export thủ công qua ZAP UI: Report > Export."
        )
        return []

    zap = ZAPv2(apikey=ZAP_API_KEY, proxies={"http": ZAP_API_URL, "https": ZAP_API_URL})
    all_urls = zap.core.urls()
    target_urls = [u for u in all_urls if TARGET_HOST in u]

    with open(path_json, "w", encoding="utf-8") as f:
        json.dump(target_urls, f, indent=2, ensure_ascii=False)

    with open(path_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["url", "path", "is_api"])
        for u in target_urls:
            p = urlparse(u).path
            writer.writerow([u, p, str(p.startswith(("/rest", "/api")))])

    print(f"[zap] {len(target_urls)} URL -> {path_json}, {path_csv}")
    return target_urls


async def main():
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=True,
        initial_action=initial_action,
        extend_system_message=extend_system_message,
    )

    try:
        result = await agent.run(max_steps=MAX_STEPS)
    finally:
        # đảm bảo browser luôn đóng dù agent lỗi giữa chừng
        await browser.close()

    print(result)

    agent_log_path = OUTPUT_DIR / f"agent_urls_{RUN_ID}.json"
    agent_urls = export_agent_log(result, agent_log_path)

    zap_json_path = OUTPUT_DIR / f"zap_urls_{RUN_ID}.json"
    zap_csv_path = OUTPUT_DIR / f"zap_urls_{RUN_ID}.csv"
    zap_urls = export_zap_sitemap(zap_json_path, zap_csv_path)

    # So sánh 2 nguồn - đây chính là số liệu "giá trị" cho survey:
    # endpoint nào chỉ ZAP (traffic thật) mới thấy mà agent log không "biết" nó đã trigger
    if zap_urls:
        hidden_endpoints = set(zap_urls) - set(agent_urls)
        print(
            f"\n[so sánh] {len(hidden_endpoints)} endpoint chỉ phát hiện qua proxy "
            f"(agent không nhận biết, ví dụ các XHR/API call ngầm):"
        )
        for u in sorted(hidden_endpoints)[:20]:
            print(f"  - {u}")


if __name__ == "__main__":
    asyncio.run(main())
