import requests
import time
import random
from bs4 import BeautifulSoup

def obter_preco_amazon(url: str, tentativas: int = 3) -> float | None:
    """
    Tenta extrair o preço de um produto da Amazon Brasil.
    Faz até `tentativas` tentativas com delays aleatórios entre elas.
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
    session = requests.Session()
    session.headers.update(headers)

    for tentativa in range(1, tentativas + 1):
        try:
            resp = session.get(url, timeout=10)
            print(f"[amazon] status={resp.status_code}, tentativa={tentativa}")
            resp.raise_for_status()
        except Exception as e:
            print(f"[amazon] erro na requisição: {e}")
            if tentativa < tentativas:
                time.sleep(random.uniform(1, 3))
            continue

        soup = BeautifulSoup(resp.content, 'html.parser')
        # Seletores principais de preço
        bloco = (
            soup.find('span', id='priceblock_ourprice')
            or soup.find('span', id='priceblock_dealprice')
            or soup.find('span', id='priceblock_saleprice')
            or soup.select_one('span.a-offscreen')
        )

        # Fallback: montar preço a partir de a-price-whole e a-price-fraction
        if not bloco:
            container = soup.select_one('span.a-price') or soup.select_one('div.a-price')
            if container:
                whole = container.select_one('span.a-price-whole')
                frac = container.select_one('span.a-price-fraction')
                if whole and frac:
                    texto_preco = whole.get_text().strip() + '.' + frac.get_text().strip()
                    # Criar um objeto temporário com método get_text
                    class Temp:
                        def __init__(self, text):
                            self.text = text
                        def get_text(self):
                            return self.text
                    bloco = Temp(texto_preco)

        if bloco:
            texto = bloco.get_text().strip()
            # Normaliza: remove 'R$', pontos de milhar e trocar ',' por '.'
            texto = texto.replace('R$', '').replace('.', '').replace(',', '.').strip()
            try:
                return float(texto)
            except ValueError:
                print(f"[amazon] falha ao converter texto para float: {texto}")
                return None

        # Se não encontrou e ainda há tentativas, espera antes de tentar de novo
        if tentativa < tentativas:
            time.sleep(random.uniform(1, 3))

    print(f"[amazon] não foi possível obter o preço após {tentativas} tentativas: {url}")
    return None
