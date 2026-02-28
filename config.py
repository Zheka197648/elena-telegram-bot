import os

BOT_TOKEN = os.getenv('BOT_TOKEN')
ELENA_CHAT_ID = os.getenv('ELENA_CHAT_ID')
SITE_URL = os.getenv('SITE_URL', 'https://elena-realtor.pages.dev')

if not BOT_TOKEN or not ELENA_CHAT_ID:
    raise ValueError("Не заданы BOT_TOKEN или ELENA_CHAT_ID!")