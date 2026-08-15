import os
import requests
from dotenv import load_dotenv
from firecrawl import FirecrawlApp
from pydantic import BaseModel, Field

# --- CẤU HÌNH ---
load_dotenv()
api_key = os.getenv("FIRECRAWL_API_KEY")

if not api_key:
    print("❌ Lỗi: Chưa cấu hình API Key trong file .env")
    exit()

app = FirecrawlApp(api_key=api_key)
NGROK_API_URL = "http://localhost:4040/api/requests/http?limit=1000"

# --- SCHEMA CHO AI AGENT ---
class DiscoveredLinks(BaseModel):
    links: list[str] = Field(description="Danh sách các URL tìm thấy trên giao diện web")
    actions_taken: list[str] = Field(description="Các hành động AI đã thực hiện (click, scroll...)")

# --- BƯỚC 1: AI TƯƠNG TÁC GIAO DIỆN ---
def agent_stimulate_traffic(target_url):
    print(f"\n[PHASE 1] 🤖 Đang kích hoạt AI Agent để tương tác với: {target_url}")
    print("⏳ Vui lòng đợi, Agent đang lướt web, click menu và kích hoạt các API ngầm...")

    try:
        agent_result = app.agent(
            prompt=(
                "Hãy đóng vai trò một chuyên gia thu thập dữ liệu. "
                "Truy cập vào trang web, thực hiện cuộn trang (scroll), nhấn vào các menu điều hướng "
                "và tìm tất cả các liên kết (URL) dẫn đến các bài viết, dự án hoặc tài liệu. "
                "Cố gắng click vào nhiều thành phần nhất có thể để kích hoạt dữ liệu ẩn."
            ),
            urls=[target_url],
            schema=DiscoveredLinks,
            model="spark-1-pro",
        )

        if agent_result.success and hasattr(agent_result, "data"):
            data = agent_result.data
            ui_urls = data.get("links", [])
            actions = data.get("actions_taken", [])
            
            print(f"✅ AI đã thao tác xong. Các hành động: {', '.join(actions)}")
            return sorted(list(set(ui_urls)))
        else:
            print("❌ Agent không trả về dữ liệu.")
            return []
            
    except Exception as e:
        print(f"🚨 Lỗi hệ thống Agent: {e!s}")
        return []

# --- BƯỚC 2: TRÍCH XUẤT NETWORK TRAFFIC TỪ NGROK ---
def extract_ngrok_endpoints():
    print(f"\n[PHASE 2] 📡 Đang đánh chặn Network Traffic từ Ngrok API...")

    try:
        response = requests.get(NGROK_API_URL)
        if response.status_code != 200:
            print(f"❌ Lỗi khi gọi API Ngrok. Status code: {response.status_code}")
            return []

        data = response.json()
        requests_list = data.get("requests", [])
        print(f"🔍 Tìm thấy {len(requests_list)} request trong lịch sử hầm ngrok.")

        unique_endpoints = set()

        for req in requests_list:
            request_data = req.get("request", {})
            method = request_data.get("method", "")
            uri = request_data.get("uri", "")
            
            if method and uri:
                # Bỏ qua các file tĩnh để danh sách API sạch hơn (Tùy chọn)
                if not uri.endswith(('.png', '.jpg', '.jpeg', '.svg', '.css', '.js', '.woff2')):
                    # Format giống Ground Truth: "GET - /api/Products"
                    endpoint_format = f"{method.upper()} - {uri.split('?')[0]}" 
                    unique_endpoints.add(endpoint_format)

        sorted_endpoints = sorted(unique_endpoints)
        return sorted_endpoints

    except Exception as e:
        print(f"🚨 Lỗi Ngrok: {e!s}")
        return []

# --- CHẠY QUY TRÌNH ---
if __name__ == "__main__":
    TARGET_URL = "https://multispinous-juliann-soberly.ngrok-free.dev/#/"
    
    # 1. Kích hoạt AI Agent để tạo ra traffic
    ui_links = agent_stimulate_traffic(TARGET_URL)
    
    # 2. Thu thập lại toàn bộ traffic đó từ Ngrok
    backend_endpoints = extract_ngrok_endpoints()
    
    # 3. Lưu kết quả Front-end
    if ui_links:
        with open("agent_ui_links.txt", "w", encoding="utf-8") as f:
            f.writelines(f"{url}\n" for url in ui_links)
        print(f"📂 Đã lưu {len(ui_links)} UI links vào: agent_ui_links.txt")

    # 4. Lưu kết quả Back-end (Server Endpoints)
    if backend_endpoints:
        with open("ngrok_backend_endpoints.txt", "w", encoding="utf-8") as f:
            f.writelines(f"{ep}\n" for ep in backend_endpoints)
        print(f"📂 Đã lưu {len(backend_endpoints)} Server Endpoints vào: ngrok_backend_endpoints.txt")