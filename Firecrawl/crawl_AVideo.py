import os

from dotenv import load_dotenv
from firecrawl import Firecrawl

load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit(1)

app = Firecrawl(api_key=api_key)

# Toàn bộ Cookie phiên đăng nhập của AVideo từ trình duyệt
AVIDEO_COOKIE = (
    "key=value; "
    "yptDeviceID=0e650df4-348a-461b-a692-119599a43812; "
    "menuCompressed=false; "
    "timezone=Asia/Saigon; "
    "autoplay=false; "
    "loadVideosListPagerowCount=10; "
    "loadVideosListPagesortBy=titleAZ; "
    "beforeinstallprompt=1; "
    "PHPSESSID=aul5avou4ehlqm7rqpnt7jjvrl; "
    "84b11d010cced71edffee7aa62c4eda0=jqm5lttsc158nib13lt4crrfuv; "
    "menuOpen=true"
)


def deep_discovery_crawl(target_url: str):
    print(f"🕵️‍♂️ Đang kích hoạt Deep Crawl tại: {target_url}")

    # Cấu hình headers kèm Cookie xác thực
    custom_headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Cookie": AVIDEO_COOKIE,
    }

    try:
        crawl_result = app.crawl(
            url=target_url,
            allow_external_links=False,
            max_discovery_depth=15,
            limit=1000,
            crawl_entire_domain=True,
            sitemap="skip",
            scrape_options={
                "formats": ["links"],  # Yêu cầu trích xuất toàn bộ link trong DOM
                "headers": custom_headers,
                "wait_for": 5000,
            },
        )

        pages = getattr(crawl_result, "data", None)
        if isinstance(crawl_result, dict):
            pages = crawl_result.get("data")

        if pages:
            unique_urls = set()
            print(f"🔄 Crawler đã quét thành công {len(pages)} trang.")

            for page in pages:
                source_url = None

                if hasattr(page, "metadata") and page.metadata:
                    source_url = getattr(page.metadata, "source_url", None) or getattr(
                        page.metadata, "sourceURL", None
                    )
                elif isinstance(page, dict) and "metadata" in page:
                    meta = page.get("metadata") or {}
                    source_url = meta.get("source_url") or meta.get("sourceURL")

                if not source_url:
                    source_url = getattr(page, "url", None) or (
                        page.get("url") if isinstance(page, dict) else None
                    )

                if source_url:
                    unique_urls.add(source_url)

            all_urls = sorted(unique_urls)

            print("\n✅ Đã hoàn tất!")
            print(f"📊 TỔNG SỐ URL TÌM THẤY VÀ CRAWL ĐƯỢC: {len(all_urls)}")

            output_file = "avideo_crawl_urls.txt"
            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(f"{url}\n" for url in all_urls)

            print(f"📂 Danh sách đã lưu tại: {output_file}")

        else:
            print("❌ Không tìm thấy dữ liệu")
            print(f"Trạng thái trả về: {crawl_result}")

    except Exception as e:
        print(f"🚨 Lỗi hệ thống: {e!s}")


if __name__ == "__main__":
    TARGET_URL = "https://possibilities-spider-flying-tenant.trycloudflare.com"
    deep_discovery_crawl(TARGET_URL)