import re

def clean_amazon_url(url: str) -> str:
    """
    Recebe uma URL de afiliado ou qualquer link da Amazon e
    retorna a URL limpa no formato https://www.amazon.com.br/dp/<ASIN>
    Se não encontrar o ASIN, retorna a URL original.
    """
    # Tenta extrair o ASIN (10 caracteres alfanuméricos)
    match = re.search(r'/dp/([A-Z0-9]{10})', url)
    if not match:
        match = re.search(r'/gp/product/([A-Z0-9]{10})', url)
    if match:
        asin = match.group(1)
        return f"https://www.amazon.com.br/dp/{asin}"
    return url
