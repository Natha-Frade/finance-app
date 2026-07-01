"""
Busca preços atuais de mercado.
- Cripto: CoinGecko (gratuito, sem API key)
- Ações/FIIs (B3): Brapi (gratuito, sem API key pra cotação básica)
- Tesouro Direto: não tem cotação "de mercado" igual ação; o valor é calculado
  pela rentabilidade do título. Aqui usamos uma aproximação simples (ajuste manual
  ou taxa fixa), já que a API oficial do Tesouro exige parsing de XML/CSV.
"""
import requests

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
}


def preco_cripto(simbolo: str) -> float:
    """Retorna o preço atual em BRL de uma criptomoeda."""
    coin_id = COINGECKO_IDS.get(simbolo.upper(), simbolo.lower())
    url = "https://api.coingecko.com/api/v3/simple/price"
    resp = requests.get(url, params={"ids": coin_id, "vs_currencies": "brl"}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data[coin_id]["brl"]


def preco_acao_fii(ticker: str) -> float:
    """Retorna o preço atual de uma ação ou FII listado na B3 via Brapi."""
    url = f"https://brapi.dev/api/quote/{ticker}"
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data["results"][0]["regularMarketPrice"]


def buscar_preco(tipo: str, ticker: str) -> float:
    """Roteador genérico: decide qual API chamar de acordo com o tipo do investimento."""
    if tipo == "cripto":
        return preco_cripto(ticker)
    elif tipo in ("fii", "acao"):
        return preco_acao_fii(ticker)
    elif tipo in ("tesouro_selic", "tesouro_ipca"):
        raise NotImplementedError(
            "Cotação de Tesouro Direto requer parsing da API oficial "
            "(https://www.tesourodireto.com.br/json/br/com/b3/tesourodireto/"
            "service/api/treasurybondsinfo.json) — pode ser adicionado depois."
        )
    raise ValueError(f"Tipo de investimento desconhecido: {tipo}")
