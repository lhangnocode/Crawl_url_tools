import os
import json
from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# 1. Tải API Key
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

app = FirecrawlApp(api_key=api_key)

def count_blog_urls(target_url):
    print(f"⚡ Đang quét (Map) danh sách URL từ: {target_url}...")

    try:
        # SỬ DỤNG TÍNH NĂNG MAP: Nhanh hơn Crawl gấp nhiều lần vì không tải nội dung
        map_result = app.map_url(target_url)

        if map_result.get('success'):
            raw_links = map_result.get('links', [])
            
            # Lọc chỉ lấy các URL thực sự nằm trong danh sách link trả về
            # (Map trả về danh sách object, chúng ta chỉ cần lấy trường 'url')
            all_urls = [item.get('url') for item in raw_links]

            # Bước lọc quan trọng: Đảm bảo chỉ đếm các link thuộc về /blog
            # (Vì đôi khi map có thể trả về cả link trang chủ hoặc link điều hướng khác)
            blog_urls = [url for url in all_urls if "/blog" in url]

            # Loại bỏ trùng lặp (nếu có)
            unique_blog_urls = list(set(blog_urls))
            total_count = len(unique_blog_urls)

            print(f"\n✅ Đã hoàn tất quét!")
            print(f"📊 TỔNG SỐ URL TÌM THẤY: {total_count}")
            
            # Lưu danh sách link ra file text đơn giản để kiểm tra
            filename = "list_urls_only.txt"
            with open(filename, "w", encoding="utf-8") as f:
                for url in unique_blog_urls:
                    f.write(f"{url}\n")
            
            print(f"📂 Danh sách link đã được lưu vào file: {filename}")

        else:
            print(f"❌ Lỗi khi Map: {map_result.get('error')}")

    except Exception as e:
        print(f"🚨 Lỗi hệ thống: {str(e)}")

if __name__ == "__main__":
    # URL cần đếm
    TARGET_URL = "https://www.firecrawl.dev/blog"
    count_blog_urls(TARGET_URL)