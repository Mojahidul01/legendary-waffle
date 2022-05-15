from telethon import TelegramClient

api_id = "4037824"
api_hash = "088d9796ffcb8857f345d66fe484e692"
bot_token = "2126552476:AAGjFXrV0hsz5JmKIzdJBdcDEctl02MmtIA"

bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)