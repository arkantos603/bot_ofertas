from scraper import obter_preco_amazon

test_urls = [
    "https://www.amazon.com.br/dp/B07MFM2TK4/",
    "https://www.amazon.com.br/dp/B09VVJGY38/",
    "https://www.amazon.com.br/dp/B07V2PBWGK/"
]

for u in test_urls:
    preco = obter_preco_amazon(u)
    print(f"{u} → {preco}")
