import os

from dotenv import load_dotenv
from firecrawl import Firecrawl  # Tên class chuẩn theo Document mới nhất

load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

# Khởi tạo client
app = Firecrawl(api_key=api_key)

JUICE_SHOP_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJkYXRhIjp7ImlkIjoyNCwidXNlcm5hbWUiOiIiLCJlbWFpbCI6ImxoYW5nMTgwMjIwMDVAZ21haWwuY29tIiwicGFzc3dvcmQiOiIzMzUzODc1ZTY3ZGE1YzZjYmU2NDY3NWFmZTQwMzUyYyIsInJvbGUiOiJjdXN0b21lciIsImRlbHV4ZVRva2VuIjoiIiwibGFzdExvZ2luSXAiOiIwLjAuMC4wIiwicHJvZmlsZUltYWdlIjoiL2Fzc2V0cy9wdWJsaWMvaW1hZ2VzL3VwbG9hZHMvZGVmYXVsdC5zdmciLCJ0b3RwU2VjcmV0IjoiIiwiaXNBY3RpdmUiOnRydWUsImNyZWF0ZWRBdCI6IjIwMjYtMDctMjkgMTE6MjQ6MDAuMjU3ICswMDowMCIsInVwZGF0ZWRBdCI6IjIwMjYtMDctMjkgMTE6MjQ6MDAuMjU3ICswMDowMCIsImRlbGV0ZWRBdCI6bnVsbH0sImJpZCI6NiwiaWF0IjoxNzg1MzI0MjQ2fQ.x-gv_z08eyanl7EsfOlVPoCvfz1alEQ0GDmRDci7mi81-Qi5woaOWNl8tLN7TVG7Nq_QijJRA-ptPCbTL9VvCpyj5b85f6b0LaIcQTPKvWUnKmhZNiwjWCGXq65SGi-4EmiwUNUWSeRxGV0U3iBaZ4oCo9yAasdVZp5603CMsNk"


def deep_discovery_crawl(target_url):
    print(f"🕵️‍♂️ Đang kích hoạt Deep Crawl tại: {target_url}")

    try:
        # Gọi API crawl và đợi kết quả (Tự động pagination theo Doc)
        crawl_result = app.crawl(
            url=target_url,
            allow_external_links=False,
            max_discovery_depth=20,
            limit=1000,
            crawl_entire_domain=True,  # QUAN TRỌNG: Quét toàn bộ nội bộ domain thay vì chỉ URL con
            sitemap="skip",  # Bỏ qua sitemap vì localhost SPA không cần
            scrape_options={
                # Chỉ cần lấy metadata, không cần parse HTML/Markdown cho nhẹ
                "formats": [],
                "headers": {
                    "ngrok-skip-browser-warning": "true",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                    # THÊM HEADER AUTHORIZATION ĐỂ XÁC THỰC VỚI JUICE SHOP
                    "Authorization": f"Bearer {JUICE_SHOP_TOKEN}",
                    # Bổ sung thêm Cookie nếu Juice Shop yêu cầu (có thể bỏ qua nếu Bearer token đã đủ)
                    "Cookie": f"token={JUICE_SHOP_TOKEN}; language=en",
                },
            },
        )

        # Kiểm tra object trả về có chứa dữ liệu data không
        if hasattr(crawl_result, "data"):
            unique_urls = set()
            print(f"🔄 Crawler đã quét thành công {len(crawl_result.data)} trang.")

            for page in crawl_result.data:
                # Trích xuất URL CHÍNH THỨC của trang đã được crawl từ metadata
                source_url = None
                if hasattr(page, "metadata") and page.metadata:
                    # Lấy qua thuộc tính (Python Object)
                    source_url = getattr(page.metadata, "source_url", None)
                elif isinstance(page, dict) and "metadata" in page:
                    # Lấy qua Dict (fallback)
                    source_url = page["metadata"].get("sourceURL")

                if source_url:
                    unique_urls.add(source_url)

            all_urls = sorted(unique_urls)

            print("\n✅ Đã hoàn tất!")
            print(f"📊 TỔNG SỐ URL TÌM THẤY VÀ CRAWL ĐƯỢC: {len(all_urls)}")

            filename = "all_crawled_urls.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.writelines(f"{url}\n" for url in all_urls)

            print(f"📂 Danh sách đã lưu tại: {filename}")

        else:
            print("❌ Không tìm thấy dữ liệu")
            print(f"Trạng thái trả về: {crawl_result}")

    except Exception as e:
        print(f"🚨 Lỗi hệ thống: {e!s}")


if __name__ == "__main__":
    TARGET_URL = "https://multispinous-juliann-soberly.ngrok-free.dev"
    deep_discovery_crawl(TARGET_URL)
