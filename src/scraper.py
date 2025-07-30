import requests
import time
import random
from bs4 import BeautifulSoup

def obter_preco_amazon(url: str, tentativas: int = 10) -> float | None:
    """
    Extrai o preco principal de um produto da Amazon Brasil.
    Tenta seletivamente os blocos principais e usa fallback confiavel.
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
            time.sleep(random.uniform(1, 2))
            continue

        soup = BeautifulSoup(resp.content, 'html.parser')

        seletores = [
            'div#corePrice_feature_div span.a-offscreen',
            'span#price_inside_buybox',
            'span#sns-base-price',
            'span#priceblock_dealprice',
            'span#priceblock_ourprice',
            'span.a-price > span.a-offscreen'
        ]

        for seletor in seletores:
            bloco = soup.select_one(seletor)
            if bloco:
                texto = bloco.get_text().replace("R$", "").replace("\xa0", "").strip()
                try:
                    preco = float(texto.replace(".", "").replace(",", "."))
                    if preco > 10 and preco < 10000:
                        return preco
                except:
                    continue

        print(f"[amazon] tentativa {tentativa}: nenhum preço confiável extraído")
        time.sleep(random.uniform(1, 2))

    print(f"[amazon] não foi possível obter o preço após {tentativas} tentativas: {url}")
    return None

def obter_preco_ml(url: str, tentativas: int = 10) -> float | None:
    """
    Extrai o preço de um produto do Mercado Livre Brasil.
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
            print(f"[ml] status={resp.status_code}, tentativa={tentativa}")
            resp.raise_for_status()
        except Exception as e:
            print(f"[ml] erro na requisição: {e}")
            time.sleep(random.uniform(1, 2))
            continue

        soup = BeautifulSoup(resp.content, 'html.parser')

        inteiro = soup.select_one("span.andes-money-amount__fraction")
        centavos = soup.select_one("span.andes-money-amount__cents")

        if inteiro:
            texto = inteiro.get_text().strip()
            if centavos:
                texto += "." + centavos.get_text().strip()
            else:
                texto += ".00"

            try:
                preco = float(texto.replace(".", "").replace(",", "."))
                if preco > 10 and preco < 10000:
                    return preco
            except:
                pass

        print(f"[ml] tentativa {tentativa}: nenhum preço confiável extraído")
        time.sleep(random.uniform(1, 2))

    print(f"[ml] não foi possível obter o preço após {tentativas} tentativas: {url}")
    return None
