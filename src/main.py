import os
import asyncio
from dotenv import load_dotenv
from scraper import obter_preco_amazon
from utils import clean_amazon_url
from telegram import Bot

load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT_ID:
    raise ValueError("Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no .env")

async def enviar_alerta(mensagem: str):
    bot = Bot(token=TOKEN)
    await bot.send_message(chat_id=CHAT_ID, text=mensagem)

async def verificar_e_notificar():
    # 1) Carrega o CSV manualmente
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "itens.csv")
    with open(csv_path, encoding='utf-8') as f:
        linhas = f.read().splitlines()

    # 2) Remove cabeçalho
    if linhas:
        linhas.pop(0)

    # 3) Para cada item
    for line in linhas:
        if not line.strip():
            continue
        try:
            # a) separa a última vírgula (desconto)
            rest, desconto_str = line.rsplit(',', 1)
            # b) separa nome (pode conter vírgulas) e url (não contém vírgula)
            nome, url_raw = rest.split(',', 1)
            desconto_min = float(desconto_str)
        except Exception as e:
            print(f"❌ Erro ao parsear linha: {line!r}\n   → {e}")
            continue

        url = clean_amazon_url(url_raw)
        preco_original = None  # Se quiser você pode adicionar coluna preco_original no CSV e extraí-la aqui.

        preco_atual = obter_preco_amazon(url)
        if preco_atual is None:
            print(f"❌ Falha no scraping de {nome}: {url}")
            continue

        # Se você tiver preco_original no CSV, descomente a linha abaixo e remova o placeholder acima.
        # desconto = (preco_original - preco_atual) / preco_original * 100

        # Para testar, vamos só enviar sempre:
        mensagem = (
            f"🛒 *{nome.strip()}* em promoção!\n"
            f"Preço encontrado: R${preco_atual:.2f}\n\n"
            f"{url}"
        )
        await enviar_alerta(mensagem)
        print(f"✅ Alerta enviado para {nome.strip()}")

def main():
    asyncio.run(verificar_e_notificar())

if __name__ == "__main__":
    main()
