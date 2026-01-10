import asyncio
import os
import logging # Thêm thư viện logging
import sys

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, Browser
from pydantic import ConfigDict, SecretStr

# --- 1. BẬT LOGGING ĐỂ XEM AI TRẢ LỜI CÁI GÌ (DEBUG) ---
# Nó sẽ in ra dòng "LLM response: ..." giúp bạn biết tại sao lỗi
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
# Tắt bớt log rác của thư viện khác
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

TASK_SCENARIO = """
1. Go to http://127.0.0.1:3000/
2. WAIT 5 SECONDS for rendering.
3. OBJECTIVE: Extract URLs.
4. ACTION: Click 'Marketplace' in the menu, wait for load, then read the URL.
"""

class PermissiveGemini(ChatGoogleGenerativeAI):
    model_config = ConfigDict(extra='allow') 
    provider: str = "google"
    @property
    def model_name(self): return self.model
    @model_name.setter
    def model_name(self, value): self.model = value

async def main():
    # --- 2. ĐỔI MODEL SANG BẢN ỔN ĐỊNH HƠN ---
    # Thử 'gemini-1.5-pro' (thông minh nhất) 
    # Hoặc 'gemini-1.5-flash' (ổn định hơn bản 2.5 experimental)
    print(">>> Đang khởi tạo Model Gemini 1.5 Pro...")
    llm = PermissiveGemini(
        model="gemini-1.5-pro", 
        api_key=SecretStr(API_KEY),
        temperature=0.0 # Ép AI nghiêm túc, không sáng tạo lung tung
    )

    browser = Browser(
        headless=False,
        disable_security=True,
    )

    agent = Agent(
        task=TASK_SCENARIO,
        llm=llm,
        browser=browser,
        use_vision=True, 
    )

    print(">>> Đang chạy (Chế độ Debug)...")
    
    try:
        await agent.run()
        print(">>> Hoàn tất.")
    except Exception as e:
        print(f"Lỗi: {e}")
    finally:
        input("Nhấn Enter để đóng trình duyệt...")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())