# src/scraper.py
import requests
from bs4 import BeautifulSoup

def obter_preco_amazon(url: str) -> float | None:
    """
    Tenta extrair o preço de um produto da Amazon Brasil.
    Retorna float ou None se não encontrar.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/91.0.4472.124 Safari/537.36'
        ),
        'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8'
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except Exception:
        return None

    soup = BeautifulSoup(resp.content, 'html.parser')

    # 1) priceblock_ourprice
    bloco = soup.find('span', id='priceblock_ourprice')
    # 2) priceblock_dealprice (promoção)
    if not bloco:
        bloco = soup.find('span', id='priceblock_dealprice')
    # 3) qualquer span com classe a-offscreen (fallback genérico)
    if not bloco:
        bloco = soup.select_one('span.a-offscreen')

    if not bloco:
        return None

    texto = bloco.get_text().strip()
    # Normaliza: remove 'R$', pontos de milhar e trocar ',' por '.'
    texto = texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return float(texto)
    except ValueError:
        return None
