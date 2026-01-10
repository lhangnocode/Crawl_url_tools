from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio

load_dotenv()

async def main():
    llm = ChatGoogle(model="gemini-2.5-flash")
    task = "I want to find the 3 newest news in devops.vn website."
    agent = Agent(task=task, llm=llm)
    await agent.run()
               
if __name__ == "__main__":
    asyncio.run(main())                       
