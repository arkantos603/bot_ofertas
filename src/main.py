import os
import re
import asyncio
import json
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

def tornar_alta_resolucao(url: str) -> str:
    """Remove sufixos ._AC_*_ para obter a imagem em alta resolução."""
    return re.sub(r'\._AC_[^\.]+', '', url)

def obter_imagem_amazon(url: str) -> str | None:
    """
    Extrai a URL da imagem principal de um produto na Amazon,
    retornando sempre a versão em alta resolução.
    """
    headers = {'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/91.0.4472.124 Safari/537.36'
    )}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')

    # 0) fallback colorImages -> hiRes dentro de um <script>
    script = soup.find('script', text=re.compile(r'colorImages'))
    if script:
        m = re.search(r'"hiRes"\s*:\s*"([^"]+)"', script.string or "")
        if m:
            return tornar_alta_resolucao(m.group(1))

    # 1) JSON dinâmico em data-a-dynamic-image
    img = soup.find('img', id='landingImage')
    if img:
        dyn = img.get('data-a-dynamic-image')
        if dyn:
            try:
                data = json.loads(dyn)
                raw = next(iter(data.keys()), None)
                if raw:
                    return tornar_alta_resolucao(raw)
            except:
                pass
        hires = img.get('data-old-hires')
        if hires:
            return tornar_alta_resolucao(hires)
        src = img.get('src')
        if src:
            return tornar_alta_resolucao(src)

    # 2) JSON‑LD
    for script in soup.find_all('script', type='application/ld+json'):
        try:
            ld = json.loads(script.string or "{}")
            img_data = ld.get("image")
            if isinstance(img_data, str):
                return tornar_alta_resolucao(img_data)
            if isinstance(img_data, list) and img_data:
                return tornar_alta_resolucao(img_data[0])
        except:
            continue

    # 3) meta og:image
    for prop in ("og:image:secure_url", "og:image"):
        meta = soup.find('meta', property=prop)
        if meta and meta.get('content'):
            return tornar_alta_resolucao(meta['content'])

    # 4) link rel="image_src"
    link = soup.find('link', rel='image_src')
    if link and link.get('href'):
        return tornar_alta_resolucao(link['href'])

    # 5) fallback wrapper
    wrapper = soup.select_one('#imgTagWrapperId img')
    if wrapper and wrapper.get('src'):
        return tornar_alta_resolucao(wrapper['src'])

    return None

async def enviar_alerta(
    mensagem: str,
    photo_url: str,
    max_tentativas: int = 7
) -> bool:
    """
    Envia sempre via send_photo; se falhar, tenta até max_tentativas vezes.
    """
    for tentativa in range(1, max_tentativas + 1):
        try:
            print(f"[telegram] enviando foto (tentativa {tentativa}): {photo_url}")
            await bot.send_photo(
                chat_id=CHAT_ID,
                photo=photo_url,
                caption=mensagem,
                parse_mode="Markdown"
            )
            return True
        except TelegramError as e:
            print(f"[telegram] erro na tentativa {tentativa}: {e}")
            if tentativa < max_tentativas:
                await asyncio.sleep(3)
    print(f"[telegram] falhou após {max_tentativas} tentativas")
    return False

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

        # tenta extrair imagem até 5 vezes antes de desistir
        imagem_url = None
        for img_tent in range(1, 8):
            imagem_url = obter_imagem_amazon(url)
            print(f"[imagem] tentativa {img_tent} para '{nome.strip()}': {imagem_url!r}")
            if imagem_url:
                break
            await asyncio.sleep(3)

        if not imagem_url:
            print(f"❌ Não foi possível obter imagem para {nome.strip()}, pulando envio")
            continue

        mensagem = (
            f"🛒 *{nome.strip()}* em promoção!\n"
            f"Preço encontrado: R${preco_atual:.2f}\n\n"
            f"{url}"
        )

        enviado = await enviar_alerta(mensagem, photo_url=imagem_url)
        if enviado:
            print(f"✅ Alerta enviado para {nome.strip()}")
            await asyncio.sleep(3)
        else:
            print(f"❌ Não foi possível enviar o alerta de foto para {nome.strip()}")

def main():
    asyncio.run(verificar_e_notificar())

if __name__ == "__main__":
    main()
