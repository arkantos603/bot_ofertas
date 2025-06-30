import re
import spacy

# Carrega o modelo de português
nlp = spacy.load("pt_core_news_sm")

def extrair_produto_preco(frase):
    frase_original = frase.lower()

    # Extrai valor numérico (R$, reais, etc.)
    preco = None
    preco_valor = None
    match = re.search(r'(\d+[\.,]?\d*)\s*(reais|r\$)?', frase_original)
    if match:
        preco_valor = match.group(1).replace(',', '.')
        preco = float(preco_valor)

    # Remove o número do preço da frase (se encontrado)
    frase_sem_preco = frase_original.replace(match.group(0), '') if match else frase_original

    # Analisa a frase com spaCy
    doc = nlp(frase_sem_preco)

    # Palavras a excluir
    stopwords_excluir = {"quero","queria","gosto","gostaria","barato","por","até","ate","um","reais","r$",
    "com","de","da","do","comprar","buscar","encontrar","cartão","encontre"}

    palavras_validas = [
        token.text for token in doc
        if token.text not in stopwords_excluir and not token.is_stop
    ]

    produto = ' '.join(palavras_validas).strip()

    return produto, preco
