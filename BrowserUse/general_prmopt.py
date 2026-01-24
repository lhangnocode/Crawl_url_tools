from browser_use import Agent, Browser, BrowserProfile, BrowserSession, ChatGoogle
from browser_use.browser import ProxySettings

from dotenv import load_dotenv

load_dotenv()

import asyncio



llm = ChatGoogle(model="gemini-2.5-pro")

extend_system_message = """
You are an aggressive QA Automation Tester. 
Your goal is maximize 'Code Coverage'. 
- Do not follow a happy path. 
- Try to click elements you haven't clicked before.
- If you see a Login form, use credentials: prodz18022005@gmail.com / Dinhkhang18022005 to access internal features.
- Avoid clicking 'Logout' or 'Sign out' unless you have explored everything else.
"""

# 2. Task ngắn gọn
task = """
Go to https://www.zyte.com/blog/best-web-scraping-apis-2026/. 
Explore the application deeply by finding and clicking all interactive elements. 
Map out the structure of the site by visiting every accessible URL.
"""

initial_action = [

    {'go_to_url': {'url': 'https://www.zyte.com/blog/best-web-scraping-apis-2026/', 'new_tab': True}},

    {'wait': {'seconds': 1}},    

]

browser = Browser(
       proxy=ProxySettings(
            server="http://localhost:8080",
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