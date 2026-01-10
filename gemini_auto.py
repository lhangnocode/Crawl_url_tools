import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser

# --- QUAN TRỌNG: Bản 0.11.2 dùng BrowserProfile ---
from browser_use.browser import BrowserProfile

from pydantic import ConfigDict, SecretStr

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Kịch bản (Prompt) - Tiếng Anh + Vision
TASK_SCENARIO = """
1. Go to http://localhost:3000/
2. WAIT for the page to load.
3. LOOK VISUALLY: If you see a 'Dismiss' button (Welcome banner) or 'Me want it!' (Cookie), CLICK THEM immediately to clear the screen.
4. Search for any product (e.g., 'Juice') or pick visible products.
5. Add exactly 3 different products to the basket.
6. If any popup appears blocking the view, close it first.
"""

# Wrapper class (Giữ nguyên)
class PermissiveGemini(ChatGoogleGenerativeAI):
    model_config = ConfigDict(extra='allow') 
    provider: str = "google"
    @property
    def model_name(self): return self.model
    @model_name.setter
    def model_name(self, value): self.model = value

async def main():
    # 1. Cấu hình Model
    llm = PermissiveGemini(
        model="gemini-2.5-flash", 
        api_key=SecretStr(API_KEY)
    )

    # 2. Cấu hình Browser (Kiểu cũ 0.11.2)
    # Chúng ta dùng BrowserProfile mặc định (sẽ tự mở Chrome mới)
    # Lưu ý: Bản 0.11.2 kết nối vào Chrome có sẵn hơi phức tạp, 
    # nên để nó tự mở trình duyệt mới là ổn định nhất.
    browser = Browser(
        browser_profile=BrowserProfile() 
    )

    # 3. Khởi tạo Agent
    agent = Agent(
        task=TASK_SCENARIO,
        llm=llm,
        browser=browser,
        use_vision=True  # <--- BẮT BUỘC ĐỂ SỬA LỖI ITEMS
    )

    print(">>> Đang chạy Agent (Vision Mode - v0.11.2)...")
    
    try:
        await agent.run()
        print(">>> Kịch bản hoàn tất!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Lỗi: {e}")
    finally:
        # Giữ browser lại để debug
        input("Ấn Enter để đóng trình duyệt...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())