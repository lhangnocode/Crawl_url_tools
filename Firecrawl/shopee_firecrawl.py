import json
import os

from dotenv import load_dotenv
from firecrawl import FirecrawlApp

load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

app = FirecrawlApp(api_key=api_key)

def get_cookie_string(filepath="shopee_auth.json"):
    """Đọc file auth của Playwright và nối thành chuỗi Cookie chuẩn HTTP"""
    try:
        if not os.path.exists(filepath):
            print(f"⚠️ Không tìm thấy file {filepath}. Vui lòng đảm bảo file tồn tại ở cùng thư mục.")
            return ""

        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
            # Lấy danh sách cookies
            cookies = data.get('cookies', [])
            # Nối thành định dạng: name1=value1; name2=value2;...
            cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies])
            return cookie_str
    except Exception as e:
        print(f"🚨 Lỗi khi đọc file Cookie: {e}")
        return ""

def scrape_shopee_raw(target_url):
    print(f"🤖 Đang dùng Firecrawl để lấy dữ liệu thô từ: {target_url}")

    # Lấy chuỗi Cookie đã đăng nhập
    cookie_header = get_cookie_string("shopee_auth.json")

    try:
        scrape_result = app.scrape(
            target_url,
            formats=['markdown'],
            # THÊM HEADER COOKIE VÀO ĐÂY ĐỂ VƯỢT LOGIN WALL
            headers={"Cookie": cookie_header} if cookie_header else {},
            actions=[
                {"type": "wait", "milliseconds": 3000},
                {"type": "scroll", "direction": "down", "amount": 2000},
                {"type": "wait", "milliseconds": 2000},
                {"type": "scroll", "direction": "down", "amount": 2000},
                {"type": "wait", "milliseconds": 2000}
            ]
        )

        raw_data = None

        if hasattr(scrape_result, 'markdown') and scrape_result.markdown:
            raw_data = scrape_result.markdown
        elif isinstance(scrape_result, dict):
            if scrape_result.get('markdown'):
                raw_data = scrape_result['markdown']
            elif 'data' in scrape_result and 'markdown' in scrape_result['data']:
                raw_data = scrape_result['data']['markdown']

        if raw_data:
            # Kiểm tra nhanh xem có bị chuyển về trang đăng nhập nữa không
            if "Đăng nhập với mã QR" in raw_data and "Quên mật khẩu" in raw_data:
                print("❌ THẤT BẠI: Shopee vẫn ép chuyển hướng về trang Đăng nhập. Có thể Cookie đã hết hạn hoặc Firecrawl IP bị ban cứng.")
                return None

            print("\n✅ Đã thu thập xong dữ liệu thành công!")
            filename = "shopee_raw_data.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(raw_data)
            print(f"📂 Toàn bộ dữ liệu thô đã được lưu tại: {filename}")
            return raw_data
        else:
            print("\n❌ Cào dữ liệu thành công nhưng không tìm thấy nội dung Markdown.")
            return None

    except Exception as e:
        print(f"🚨 Lỗi hệ thống Firecrawl: {e!s}")
        return None

if __name__ == "__main__":
    TARGET_URL = "https://shopee.vn/search?keyword=laptop"
    scrape_shopee_raw(TARGET_URL)
