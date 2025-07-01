# src/test_notifier_async.py
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot

async def main():
    load_dotenv()
    TOKEN = os.getenv('TELEGRAM_TOKEN')
    CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    if not TOKEN or not CHAT_ID:
        raise ValueError("Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no .env")
    bot = Bot(token=TOKEN)

    # 1) obtém info do canal
    chat = await bot.get_chat(chat_id=CHAT_ID)
    print("✅ Chat OK:", chat)

    # 2) envia teste
    msg = await bot.send_message(chat_id=CHAT_ID, text="✅ Teste Async de notificação")
    print("✅ Mensagem enviada:", msg)

if __name__ == "__main__":
    asyncio.run(main())
