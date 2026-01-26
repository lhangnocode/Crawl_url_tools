from browser_use import Agent, Browser, BrowserProfile, ChatGoogle
from browser_use.browser import ProxySettings
from dotenv import load_dotenv
import asyncio

load_dotenv()

llm = ChatGoogle(model="gemini-2.5-flash")

extend_system_message = """
You are an aggressive QA Automation Tester. 
Your goal is maximize 'Code Coverage'. 
- Do not follow a happy path. 
- Try to click elements you haven't clicked before.
- If you see a Login, login with google account to access internal features.
- Avoid clicking 'Logout' or 'Sign out' unless you have explored everything else.
RULES FOR NAVIGATION:
1. Do not follow a happy path. Try to click elements you haven't clicked before.
2. If you navigate to a new page causing an error or want to return:
   - USE THE 'GO_BACK' TOOL. DO NOT USE 'CLOSE_TAB' unless you are 100% sure you opened a new tab explicitly (e.g., target="_blank").
   - Closing the main tab will crash the browser. BE CAREFUL.
3. If you see a Login, login with google account to access internal features.
"""

# 2. Task ngắn gọn
task = """
Go to https://owasp.org/www-project-benchmark/. 
Explore the application deeply by finding and clicking all interactive elements. 
Map out the structure of the site by visiting every accessible URL.
IMPORTANT: If you click a link and it opens in the SAME tab, use 'go_back' to return. ONLY use 'close_tab' if you see multiple tabs open.
"""

initial_action = [
    {'go_to_url': {'url': 'https://owasp.org/www-project-benchmark/', 'new_tab': False}},
    {'wait': {'seconds': 1}},    
]

browser = Browser(
    browser_profile=BrowserProfile(
        # 1. QUAN TRỌNG: Thuộc tính này báo cho thư viện tự động tắt các policy bảo mật
        disable_security=True,
        
        proxy=ProxySettings(
            server="http://localhost:8080",
        ),
        
        # 2. Các tham số Chromium bổ trợ (vẫn giữ để đảm bảo an toàn tuyệt đối)
        args=[
            "--ignore-certificate-errors",
            "--ignore-ssl-errors",
            "--ignore-certificate-errors-spki-list",
            "--allow-insecure-localhost",
            "--no-sandbox",
            "--disable-web-security",
            "--test-type",
            "--disable-features=IsolateOrigins,site-per-process",
            # Thêm cờ này để đảm bảo GPU không gây lỗi hiển thị khi tắt bảo mật
            "--disable-gpu" 
        ],
        
        # 3. Cấu hình Context
        new_context_config={ 
            "ignore_https_errors": True,
            "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "viewport": {'width': 1280, 'height': 720},
            "permissions": ["geolocation", "notifications"] 
        }
    )
)

async def main():
    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=True,
        initial_action=initial_action,
        extend_system_message=extend_system_message,
        # calculate_cost=True # Lưu ý: Một số version browser-use cũ có thể chưa ổn định với tính năng này, nếu lỗi hãy comment lại
    )

    result = await agent.run()

    print(result)
    # print(f"Token usage: {result.usage}") # Kiểm tra attribute usage trước khi in để tránh lỗi runtime

asyncio.run(main())