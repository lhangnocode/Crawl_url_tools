from browser_use import Agent, Browser, BrowserProfile, BrowserSession, ChatGoogle
from browser_use.browser import ProxySettings

from dotenv import load_dotenv

load_dotenv()

import asyncio



llm = ChatGoogle(model="gemini-2.5-flash")

extend_system_message = """

You are a security testing expert. 

Your task is to thoroughly explore the target website by interacting with all accessible elements. 

Click every clickable component, scroll through all sections, and navigate to every reachable page or feature. 

Perform these actions systematically to maximize security testing coverage and ensure no part of the website is overlooked.

"""

task = """

Open http://192.168.1.14:3001/ , if you see the modal click dismiss and log in with:

- Email: prodz18022005@gmail.com

- Password: Dinhkhang18022005



Then perform the following steps:



1) Choose one product and click add to Basket, look at your Basket if the count turn to 1, next to step 2.

2) Click “Your Basket”.

3) Proceed to Checkout.

4) Add a new address and fill out all address details completely.

5) Select the newly created address and click Continue.

6) Choose any delivery speed.

7) Click Continue.



You will see My Payment Options. On the “My Payment Options” page. Click on "Other payment options", then when the arrow expands, click on Spreadshirt (US) and finish the process.



"""

initial_action = [

    {'go_to_url': {'url': 'http://192.168.1.14:3001', 'new_tab': True}},

    {'wait': {'seconds': 1}},    

]

browser = Browser(
       proxy=ProxySettings(
            server="http://localhost:8081",
        )
)

async def main():

    # browser_session = BrowserSession(

    # )

    # browser_profile = BrowserProfile(

    #     proxy={

    #         "server" : "http://localhost:8080"    

    #     }

    # browser_session = BrowserSession(

    #     # executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',

    #     user_data_dir=r'C:\Users\admin\AppData\Local\Temp\scoped_dir11492_2071321393\Default'

    # )

    agent = Agent(

        task=task,

        llm=llm,

        browser=browser,

        initial_action=initial_action,

        extend_system_message=extend_system_message

    )

    result = await agent.run()

    print(result)



asyncio.run(main())