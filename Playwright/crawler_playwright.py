import asyncio
from urllib.parse import urljoin, urlparse

from playwright.async_api import async_playwright

# Cấu hình
START_URL = "http://192.168.1.14:3001/#/"  # Thay đổi URL mục tiêu của bạn ở đây
MAX_PAGES = 50  # Giới hạn số trang để test, tránh chạy vô tận
HEADLESS = False # Đặt True nếu muốn chạy ngầm (không hiện trình duyệt)

#! PLAYWRIGHT CRAWLER

async def crawl_website():
    async with async_playwright() as p:
        # Khởi tạo trình duyệt
        browser = await p.chromium.launch(headless=HEADLESS)
        # Tạo context (có thể thêm user_agent nếu cần thiết)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )
        page = await context.new_page()

        # Xác định domain gốc để không crawl sang web khác
        base_domain = urlparse(START_URL).netloc

        # Danh sách cần crawl và danh sách đã crawl
        urls_to_visit = [START_URL]
        visited_urls = set()

        print(f"🚀 Bắt đầu crawl tại: {START_URL}")

        while urls_to_visit and len(visited_urls) < MAX_PAGES:
            current_url = urls_to_visit.pop(0) # Lấy URL đầu tiên trong hàng đợi

            # Bỏ qua nếu đã visit
            if current_url in visited_urls:
                continue

            try:
                print(f"Analyzing: {current_url}")

                # Truy cập trang
                # wait_until='networkidle': Chờ đến khi không còn kết nối mạng (trang tải xong hết JS)
                await page.goto(current_url, wait_until='networkidle', timeout=60000)

                visited_urls.add(current_url)

                # --- TRÍCH XUẤT URL ---
                # Lấy tất cả thẻ <a> và thuộc tính href
                # Dùng eval_on_selector_all chạy JS trực tiếp trên trình duyệt để lấy nhanh hơn
                links = await page.eval_on_selector_all("a", "elements => elements.map(e => e.href)")

                for link in links:
                    # 1. Xử lý đường dẫn tương đối (ví dụ: /about -> https://domain.com/about)
                    absolute_link = urljoin(current_url, link)

                    # 2. Loại bỏ phần anchor (ví dụ: #section1) để tránh trùng lặp
                    absolute_link = absolute_link.split('#')[0]

                    # 3. Phân tích link
                    parsed_link = urlparse(absolute_link)

                    # 4. ĐIỀU KIỆN LỌC URL:
                    # - Phải cùng domain
                    # - Không phải là file ảnh/pdf...
                    # - Chưa từng visit
                    # - Chưa có trong hàng đợi
                    if (parsed_link.netloc == base_domain and
                        absolute_link not in visited_urls and
                        absolute_link not in urls_to_visit and
                        parsed_link.scheme in ['http', 'https']):

                        urls_to_visit.append(absolute_link)
                        # print(f"  --> Tìm thấy link mới: {absolute_link}")

            except Exception as e:
                print(f"❌ Lỗi tại {current_url}: {e}")

        print("\n" + "="*30)
        print(f"✅ Đã hoàn thành! Tổng số URL tìm thấy: {len(visited_urls)}")
        print("="*30)
        for url in visited_urls:
            print(url)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(crawl_website())
