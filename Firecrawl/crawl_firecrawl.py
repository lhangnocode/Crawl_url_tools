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
    
    try:
        # Gọi API
        crawl_result = app.crawl(
            url=target_url,
            limit=50,
            scrape_options={
                'formats': ['links'],
                #? Cố gắng gửi header để bypass ngrok warning (tùy thuộc vào version SDK hỗ trợ)
                'headers': {
                    'ngrok-skip-browser-warning': 'true',
                    'User-Agent': 'Mozilla/5.0 (compatible; FirecrawlBot/1.0)'
                }
            }
        )

        # 1. Kiểm tra nếu có dữ liệu (Firecrawl SDK trả về object có thuộc tính 'data')
        # Thay vì kiểm tra dict, ta kiểm tra xem có thuộc tính 'data' hay không
        if hasattr(crawl_result, 'data'):
            data = crawl_result.data # Truy cập bằng dấu chấm, không dùng .get()
            
            unique_urls = set()
            print(f"🔄 Đang trích xuất link từ {len(data)} trang đã quét...")

            for page in data:
                # 2. Dựa vào logs của bạn, 'links' có thể nằm trong metadata hoặc là thuộc tính trực tiếp
                # Ta sẽ thử lấy từ cả 2 nguồn cho chắc chắn
                
                # Cách lấy 1: Lấy trực tiếp nếu là dict
                if isinstance(page, dict):
                    found_links = page.get('links', [])
                    metadata_links = page.get('metadata', {}).get('links', [])
                # Cách lấy 2: Lấy qua thuộc tính nếu là Object (Document)
                else:
                    found_links = getattr(page, 'links', [])
                    metadata = getattr(page, 'metadata', None)
                    metadata_links = getattr(metadata, 'links', []) if metadata else []

                # Gộp link
                all_links = set(found_links) | set(metadata_links)

                for link in all_links:
                    if link:
                        unique_urls.add(link)

            # Lọc chỉ lấy link blog
            all_urls = sorted(unique_urls)

            print(f"\n✅ Đã hoàn tất!")
            print(f"📊 TỔNG SỐ URL TÌM THẤY: {len(all_urls)}")

            filename = "all_crawled_urls.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for url in all_urls:
                    f.write(f"{url}\n")

            print(f"📂 Danh sách đã lưu tại: {filename}")
            
        else:
            print("❌ Không tìm thấy dữ liệu (Response không có attribute 'data')")
            # In ra kiểu dữ liệu thực tế để debug nếu vẫn lỗi
            print(f"Kiểu dữ liệu trả về: {type(crawl_result)}")

    except Exception as e:
        print(f"🚨 Lỗi hệ thống: {str(e)}")

if __name__ == "__main__":
    # TARGET_URL = "https://www.firecrawl.dev/blog"
    TARGET_URL = "https://multispinous-juliann-soberly.ngrok-free.dev"
    deep_discovery_crawl(TARGET_URL)