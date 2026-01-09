import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser
# Chúng ta vẫn cần import BrowserProfile để kết nối cổng debug
from browser_use.browser import BrowserProfile 
from pydantic import ConfigDict, SecretStr

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

# Kịch bản (Prompt) - Thêm bước chờ rõ ràng hơn
TASK_SCENARIO = """
1. Go to http://localhost:3001/#/
2. WAIT 5 SECONDS for the page to fully load.
3. IMPORTANT: If you see a 'Dismiss' button (Welcome banner), click it.
4. If you see a 'Me want it!' or 'Accept' button (Cookie consent), click it.
5. Add exactly 3 different products to the basket.
6. If any popup appears, close it.
"""

# Class wrapper cho Gemini
class PermissiveGemini(ChatGoogleGenerativeAI):
    model_config = ConfigDict(extra='allow') 
    provider: str = "google"
    @property
    def model_name(self): return self.model
    @model_name.setter
    def model_name(self, value): self.model = value

async def main():
    # SỬA 1: Dùng 'gemini-1.5-pro' để thông minh hơn, tránh lỗi "items"
    # Nếu bị lỗi Quota/Rate Limit thì mới đổi về 'gemini-1.5-flash'
    llm = PermissiveGemini(
        model="gemini-1.5-pro", 
        api_key=SecretStr(API_KEY)
    )

    # SỬA 2: Kết nối vào Chrome đang mở (Port 9222)
    profile = BrowserProfile(
        cdp_url="http://127.0.0.1:9222" 
    )
    browser = Browser(browser_profile=profile)

    agent = Agent(
        task=TASK_SCENARIO,
        llm=llm,
        browser=browser
    )

    print(">>> Đang kết nối vào Chrome (Port 9222)...")
    
    try:
        await agent.run()
        print(">>> Kịch bản hoàn tất! Hãy kiểm tra ZAP.")
    except Exception as e:
        print(f"Lỗi: {e}")
    
    # SỬA 3: Xóa lệnh browser.close() vì đang dùng CDP connection
    print(">>> Đã xong nhiệm vụ. (Giữ nguyên trình duyệt)")

if __name__ == "__main__":
    asyncio.run(main())