import asyncio
from telethon import TelegramClient
import config
import os

SESSION_FILE = os.path.join('session', 'scraper_session')

async def check_latest():
    client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
    await client.start()
    
    username = 'freelance_ethio'
    try:
        msgs = await client.get_messages(username, limit=1)
        if msgs:
            print(f"Latest ID on Telegram for {username}: {msgs[0].id}")
            print(f"Text: {msgs[0].text[:100]}...")
        else:
            print(f"No messages found for {username}")
    except Exception as e:
        print(f"Error: {e}")
            
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(check_latest())
