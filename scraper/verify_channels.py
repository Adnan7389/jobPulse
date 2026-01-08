import asyncio
from telethon import TelegramClient
import config
import os

SESSION_FILE = os.path.join('session', 'scraper_session')

async def check_channels():
    client = TelegramClient(SESSION_FILE, config.API_ID, config.API_HASH)
    await client.start()
    
    usernames = ['joblens1', 'digitaljobs_et', 'freelance_ethio']
    print(f"{'Username':<20} | {'Broadcast':<10} | {'Megagroup':<10} | {'Title'}")
    print("-" * 60)
    
    for username in usernames:
        try:
            chat = await client.get_entity(username)
            is_broadcast = getattr(chat, 'broadcast', False)
            is_megagroup = getattr(chat, 'megagroup', False)
            print(f"{username:<20} | {str(is_broadcast):<10} | {str(is_megagroup):<10} | {chat.title}")
        except Exception as e:
            print(f"{username:<20} | {'ERROR':<10} | {'ERROR':<10} | {e}")
            
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(check_channels())
