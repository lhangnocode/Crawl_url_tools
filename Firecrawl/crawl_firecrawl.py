import os
import json
import time
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

app = FirecrawlApp(api_key=api_key)

def deep_discovery_crawl(target_url):
    print(f"🕵️‍♂️ Đang kích hoạt Deep Crawl (JS Rendering) tại: {target_url}")
    print("⏳ Quá trình này sẽ chậm hơn Map vì phải đợi JS tải xong...")

    try:
        # 3. Sử dụng method .crawl() như trong source code (self.crawl = self._v2_client.crawl)
        # Lưu ý: Python SDK v2 thường dùng tham số trực tiếp (limit, scrape_options)
        crawl_result = app.crawl(
            url=target_url,
            limit=50, # Giới hạn số trang để test
            scrape_options={
                'formats': ['links'], # Chỉ lấy links để tối ưu tốc độ và dung lượng
            }
        )

        # Kiểm tra kết quả
        # SDK v2 thường trả về Dict hoặc Object. Ta kiểm tra an toàn.
        if isinstance(crawl_result, dict) and crawl_result.get('success'):
            data = crawl_result.get('data', [])
            
            unique_urls = set()
            print(f"🔄 Đang trích xuất link từ {len(data)} trang đã quét...")

            for page in data:
                # Thuộc tính 'links' tồn tại do ta đã request formats=['links']
                found_links = page.get('links', [])
                
                # Gom tất cả link tìm được
                for link in found_links:
                    if link:
                        unique_urls.add(link)

            # Lọc: Chỉ giữ lại các URL thuộc về /blog
            blog_urls = [u for u in unique_urls if "/blog" in u]
            blog_urls.sort()

            print(f"\n✅ Đã hoàn tất!")
            print(f"📊 TỔNG SỐ URL BÀI VIẾT TÌM THẤY: {len(blog_urls)}")
            
            print("📝 Chuẩn bị ghi file...")

            # Xuất file
            filename = "blog_urls_v2.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for url in blog_urls:
                    f.write(f"{url}\n")
            
            print(f"📂 Danh sách đã lưu tại: {filename}")
            
        else:
            # Xử lý trường hợp API trả về lỗi
            error_msg = crawl_result.get('error') if isinstance(crawl_result, dict) else "Lỗi không xác định"
            print(f"❌ Crawl thất bại: {error_msg}")
            print(f"Chi tiết response: {crawl_result}")

    except Exception as e:
        print(f"🚨 Lỗi hệ thống: {str(e)}")

if __name__ == "__main__":
    TARGET_URL = "https://www.firecrawl.dev/blog"
    deep_discovery_crawl(TARGET_URL)