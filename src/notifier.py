from telegram import Bot
import os

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def alerta_telegram(mensagem):
    bot = Bot(token=TOKEN)
    bot.send_message(chat_id=CHAT_ID, text=mensagem)
