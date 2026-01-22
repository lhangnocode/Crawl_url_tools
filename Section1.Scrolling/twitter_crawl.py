from browser_use import Agent, Browser, BrowserProfile, BrowserSession, ChatGoogle
from browser_use.browser import ProxySettings

from dotenv import load_dotenv

load_dotenv()

import asyncio



llm = ChatGoogle(model="gemini-2.0-flash")

extend_system_message = """
You are an aggressive QA Automation Tester. 
Your goal is maximize 'Code Coverage'. 
- Do not follow a happy path. 
- Try to click elements you haven't clicked before.
- If you see a Login, login with google account to access internal features.
- Avoid clicking 'Logout' or 'Sign out' unless you have explored everything else.
"""

# 2. Task ngắn gọn
task = """
Go to https://x.com. 
Explore the application deeply by finding and clicking all interactive elements. 
Map out the structure of the site by visiting every accessible URL.
"""

initial_action = [

    {'go_to_url': {'url': 'https://x.com', 'new_tab': True}},

    {'wait': {'seconds': 1}},    

]

browser = Browser(
        browser_profile=BrowserProfile(
            proxy=ProxySettings(
                server="http://localhost:8080",
            ),
            # 2. Bổ sung thêm các args mạnh tay hơn để ép Chrome bỏ qua lỗi SSL
            extra_chromium_args=[
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                "--ignore-certificate-errors-spki-list", # Bỏ qua lỗi khóa công khai
                "--allow-insecure-localhost",
                "--no-sandbox",
                "--disable-web-security", # Tắt Same-origin policy
                "--test-type", # Giúp bỏ qua một số cảnh báo bảo mật khi khởi động
            ],
            
            # 3. Cấu hình Context: Đảm bảo ignore_https_errors được bật ở level Context
            new_context_config={ 
                "ignore_https_errors": True, # Bắt buộc phải có khi dùng Proxy
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "viewport": {'width': 1280, 'height': 720},
                # Thêm permissions để tránh popup hỏi quyền gây gián đoạn
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

        calculate_cost=True

    )

    result = await agent.run()

    print(result)

    print(f"Token usage: {result.usage}")


asyncio.run(main())