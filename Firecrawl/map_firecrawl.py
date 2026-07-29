import os

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

# 1. Tải API Key
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

app = FirecrawlApp(api_key=api_key)

#! KHONG HOAT DONG VOI SPA
def count_all_urls(target_url):
    print(f"⚡ Đang quét (Map) toàn bộ danh sách URL từ: {target_url}...")

    try:
        # SỬ DỤNG TÍNH NĂNG MAP
        map_result = app.map(target_url)

        # --- PHẦN SỬA LỖI QUAN TRỌNG ---
        # Lỗi cũ: 'MapData' object has no attribute 'get'
        # Nguyên nhân: SDK trả về Object, không phải Dict.

        # 1. Lấy danh sách links từ thuộc tính object
        # Sử dụng getattr để an toàn (nếu có thuộc tính .links thì lấy, không thì trả về list rỗng)
        if hasattr(map_result, 'links'):
            raw_links = map_result.links
        elif isinstance(map_result, dict):
             # Fallback: đề phòng trường hợp trả về dict (phiên bản cũ)
            raw_links = map_result.get('links', [])
        else:
            print("⚠️ Cảnh báo: Không tìm thấy thuộc tính 'links' trong kết quả.")
            print(f"Kiểu dữ liệu thực tế: {type(map_result)}")
            raw_links = []

        # 2. Xử lý danh sách link
        all_urls = []
        for item in raw_links:
            if isinstance(item, str):
                all_urls.append(item)
            elif isinstance(item, dict):
                url = item.get('url')
                if url: all_urls.append(url)
            # Thêm xử lý nếu item bên trong cũng là object (đề phòng)
            elif hasattr(item, 'url'):
                all_urls.append(item.url)

        # 3. Loại bỏ trùng lặp và sắp xếp
        unique_urls = list(set(all_urls))
        total_count = len(unique_urls)

        print("\n✅ Đã hoàn tất quét!")
        print(f"📊 TỔNG SỐ URL TÌM THẤY: {total_count}")

        # Lưu danh sách link ra file
        filename = "list_all_urls.txt"
        with open(filename, "w", encoding="utf-8") as f:
            for url in sorted(unique_urls):
                f.write(f"{url}\n")

        print(f"📂 Danh sách link đã được lưu vào file: {filename}")

    except Exception as e:
        print(f"🚨 Lỗi hệ thống: {e!s}")
        # In thêm dir() để debug xem object có những thuộc tính gì nếu vẫn lỗi
        try:
            print("🔍 Các thuộc tính có sẵn của object lỗi:", dir(e))
        except:
            pass

if __name__ == "__main__":
    # URL cần quét
    TARGET_URL = "https://owasp.org/www-project-benchmark/"
    count_all_urls(TARGET_URL)
