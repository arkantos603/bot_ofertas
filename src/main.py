import os
import asyncio
import json
import random
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from scraper import obter_preco_amazon
from utils import clean_amazon_url
from telegram import Bot
from telegram.error import TelegramError

load_dotenv()
TOKEN   = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT_ID:
    raise ValueError("Defina TELEGRAM_TOKEN e TELEGRAM_CHAT_ID no .env")

bot = Bot(token=TOKEN)

async def enviar_alerta(
    mensagem: str,
    photo_url: str | None = None,
    max_tentativas: int = 5
) -> bool:
    """
    Tenta enviar `mensagem` ou foto+legenda ao Telegram até `max_tentativas` vezes.
    """
    for tentativa in range(1, max_tentativas + 1):
        try:
            if photo_url:
                print(f"[telegram] tentando enviar foto: {photo_url}")
                await bot.send_photo(
                    chat_id=CHAT_ID,
                    photo=photo_url,
                    caption=mensagem,
                    parse_mode="Markdown"
                )
            else:
                print(f"[telegram] tentando enviar mensagem com preview")
                await bot.send_message(
                    chat_id=CHAT_ID,
                    text=mensagem,
                    parse_mode="Markdown"
                    # preview ativado por padrão
                )
            print(f"[telegram] envio bem‑sucedido na tentativa {tentativa}")
            return True
        except TelegramError as e:
            print(f"[telegram] erro na tentativa {tentativa}: {e}")
            if tentativa < max_tentativas:
                await asyncio.sleep(random.uniform(1, 3))
    print(f"[telegram] falhou após {max_tentativas} tentativas")
    return False

def obter_imagem_amazon(url: str) -> str | None:
    """
    Extrai a URL da imagem principal de um produto na Amazon.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, 'html.parser')

        # 1) meta tags Open Graph
        for prop in ("og:image:secure_url", "og:image"):
            meta = soup.find('meta', property=prop)
            if meta and meta.get('content'):
                print(f"[imagem] {prop} -> {meta['content']}")
                return meta['content']

        # 2) <link rel="image_src">
        link = soup.find('link', rel='image_src')
        if link and link.get('href'):
            print(f"[imagem] link[rel=image_src] -> {link['href']}")
            return link['href']

        # 3) JSON dinâmico em data-a-dynamic-image
        img = soup.find('img', id='landingImage')
        if img:
            dyn = img.get('data-a-dynamic-image')
            if dyn:
                try:
                    data = json.loads(dyn)
                    url_img = next(iter(data.keys()))
                    print(f"[imagem] data-a-dynamic-image -> {url_img}")
                    return url_img
                except Exception as e:
                    print(f"[imagem] JSON dinâmico inválido: {e}")
            # fallback hires / src
            if img.get('data-old-hires'):
                print(f"[imagem] data-old-hires -> {img['data-old-hires']}")
                return img['data-old-hires']
            if img.get('src'):
                print(f"[imagem] src -> {img['src']}")
                return img['src']

        # 4) dentro de #imgTagWrapperId
        wrapper = soup.select_one('#imgTagWrapperId img')
        if wrapper and wrapper.get('src'):
            print(f"[imagem] #imgTagWrapperId src -> {wrapper['src']}")
            return wrapper['src']

        # 5) <img class="a-dynamic-image">
        dyn_img = soup.find('img', class_='a-dynamic-image')
        if dyn_img and dyn_img.get('src'):
            print(f"[imagem] .a-dynamic-image src -> {dyn_img['src']}")
            return dyn_img['src']

        # 6) JSON‑LD (<script type="application/ld+json">)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or "{}")
                img_data = data.get("image")
                if isinstance(img_data, str) and img_data:
                    print(f"[imagem] JSON-LD image -> {img_data}")
                    return img_data
                if isinstance(img_data, list) and img_data:
                    print(f"[imagem] JSON-LD image[0] -> {img_data[0]}")
                    return img_data[0]
            except Exception:
                continue

    except Exception as e:
        print(f"[imagem] erro ao obter imagem: {e}")

    print(f"[imagem] não encontrou imagem em {url}")
    return None

async def verificar_e_notificar():
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "itens.csv")
    with open(csv_path, encoding='utf-8') as f:
        linhas = f.read().splitlines()
    if linhas:
        linhas.pop(0)

    for line in linhas:
        if not line.strip():
            continue
        try:
            rest, desconto_str = line.rsplit(',', 1)
            nome, url_raw       = rest.split(',', 1)
            desconto_min        = float(desconto_str)
        except Exception as e:
            print(f"❌ Erro ao parsear linha: {line!r}\n   → {e}")
            continue

        url = clean_amazon_url(url_raw)
        preco_atual = obter_preco_amazon(url)
        if preco_atual is None:
            print(f"❌ Falha no scraping de {nome.strip()}: {url}")
            continue

        imagem_url = obter_imagem_amazon(url)
        print(f"[imagem] URL extraída para '{nome.strip()}': {imagem_url!r}")

        mensagem = (
            f"🛒 *{nome.strip()}* em promoção!\n"
            f"Preço encontrado: R${preco_atual:.2f}\n\n"
            f"{url}"
        )

        enviado = await enviar_alerta(mensagem, photo_url=imagem_url)
        if enviado:
            print(f"✅ Alerta enviado para {nome.strip()}")
            await asyncio.sleep(random.uniform(1, 2))
        else:
            print(f"❌ Não foi possível enviar alerta para {nome.strip()}")

def main():
    asyncio.run(verificar_e_notificar())

if __name__ == "__main__":
    main()
