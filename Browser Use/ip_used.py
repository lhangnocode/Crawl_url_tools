from browser_use import Agent, Browser, BrowserProfile, BrowserSession, ChatGoogle
from browser_use.browser import ProxySettings

from dotenv import load_dotenv

load_dotenv()

import asyncio



llm = ChatGoogle(model="gemini-2.5-pro", temperature=0.0)

extend_system_message = """

You are a security testing expert. 

Your task is to thoroughly explore the target website by interacting with all accessible elements. 

Click every clickable component, scroll through all sections, and navigate to every reachable page or feature. 

Perform these actions systematically to maximize security testing coverage and ensure no part of the website is overlooked.

"""

task1 = """

Open http://192.168.1.14:3001/#/ , if you see the modal click dismiss and log in with:

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

task2 = """
GOAL: Complete the checkout process on http://192.168.1.14:3001/#/ with robust error handling.

### CRITICAL RULES (READ FIRST):
1. **Overlay/Dimmed Screen Handling:** If the screen becomes dimmed/blurred or you accidentally open a sidebar (like "Settings", "Photo Wall") that blocks the view:
   - IMMEDIATELY click on the dark background area outside the modal/sidebar to return to the main view.
   - Do NOT try to interact with elements inside the accidental modal.

2. **Popups:** Always dismiss the "Welcome to the Academy" banner ('Dismiss' button) and accept cookies ('Me want it') immediately upon loading.

### STEP-BY-STEP INSTRUCTIONS:

**PHASE 1: AUTHENTICATION (Login or Register)**
1. Navigate to the Login page.
2. Attempt to Log in with:
   - Email: prodz18022005@gmail.com
   - Password: Dinhkhang18022005
3. **CHECK FOR FAILURE:** If you see an error message (like "Invalid email or password") OR if login fails twice:
   - Click "Not yet a customer?" to go to Registration.
   - Register with the SAME credentials above.
   - Security Question: Select "Your favorite book?".
   - Answer: "Dac nhan tam"
   - Click Register.
   - After successful registration, Log in with the credentials.

**PHASE 2: SHOPPING**
4. Ensure you are logged in and on the homepage.
5. Add exactly one product to the Basket (e.g., Apple Juice).
6. Verify the "Your Basket" button shows a notification count of '1'.
7. Click "Your Basket" to view the cart.
8. Click "Checkout".

**PHASE 3: CHECKOUT FLOW**
9. **Address:** Add a new address (fill all fields with dummy data like "Vietnam", "Hanoi", Zip "10000"). Select it and click Continue.
10. **Delivery:** Choose any delivery speed (e.g., Standard) and click Continue.
11. **Payment:** - You will see "My Payment Options".
    - Click on "Other payment options" to expand the list.
    - Select "Spreadshirt (US)" (or any available 3rd party option).
    - Click "Continue" or "Place Order" to finish.

**PHASE 4: VERIFICATION**
12. Confirm the order is placed or the "Thank you" confirmation screen appears.
"""


task3 = """
GOAL: Complete the checkout process on http://192.168.1.14:3001/#/ with strict click handling.

### CRITICAL RULES:
1. **Overlay Handling:** If a sidebar or modal blocks the view, close it immediately (Click 'X' or outside area).
2. **Single Click Rule:** When selecting an item (like an Address or Payment method), click EXACTLY ONCE. Never double-click, as this will deselect the item.

### STEP-BY-STEP INSTRUCTIONS:

**PHASE 1: AUTHENTICATION**
1. Navigate to Login.
2. Attempt Login (Email: prodz18022005@gmail.com | Pass: Dinhkhang18022005).
3. **Fallback:** If Login fails/errors:
   - Click "Not yet a customer?" -> Register.
   - Question: "Your favorite book?" -> Answer: "Dac nhan tam".
   - Register -> Then Login again.

**PHASE 2: SHOPPING**
4. Add 1 product to Basket.
5. Go to "Your Basket" -> Click "Checkout".

**PHASE 3: ADDRESS SELECTION (IMPORTANT)**
6. **Add Address:** Click "Add New Address", fill details (Country: "Vietnam", Name: "Khang", Mobile: "1234567890", Zip: "10000", Address: "Hanoi"), and Submit.
7. **Select Address:** - Find the newly created address in the list.
   - Click the *radio button* or the row **EXACTLY ONE TIME**.
   - **WAIT** for the row to visually highlight/select.
   - **DO NOT CLICK IT AGAIN.**
   - Immediately click "Continue".

**PHASE 4: DELIVERY & PAYMENT**
8. **Delivery:** Select "Standard Delivery" (Click ONCE) -> Click "Continue".
9. **Payment:** - Look for "My Payment Options".
   - Click "Other payment options" to expand.
   - Select "Spreadshirt (US)" (Click ONCE).
   - Click "Continue" / "Place Order".

**PHASE 5: FINISH**
10. Verify order confirmation.
"""

initial_action = [

    {'go_to_url': {'url': 'http://192.168.1.14:3001/#/', 'new_tab': True}},

    {'wait': {'seconds': 1}},    

]

browser = Browser(
       proxy=ProxySettings(
            server="http://localhost:8080",
        )
)

async def main():

    agent = Agent(

        task=task3,

        llm=llm,

        browser=browser,

        initial_action=initial_action,

        extend_system_message=extend_system_message,

        calculate_cost=True

    )

    result = await agent.run()

    print(result)

    print(f"Token usage: {result.usage}")


asyncio.run(main())