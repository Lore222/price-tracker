import re
import time
from typing import Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

SCRAPERAPI_ENDPOINT = "https://api.scraperapi.com/"


def _get_via_scraperapi(url: str, api_key: str, timeout: int = 30):
    """Recupera la pagina passando dal proxy ScraperAPI per evitare blocchi anti-bot.

    ScraperAPI bypassa i sistemi anti-bot (verifiche captcha, rate limiting,
    controlli User-Agent) facendo la richiesta dal suo datacenter e restituendo
    l'HTML pulito della pagina richiesta.
    """
    payload = {
        "api_key": api_key,
        "url": url,
    }
    return requests.get(SCRAPERAPI_ENDPOINT, params=payload, timeout=timeout)


def _parse_price(text: Optional[str]) -> Optional[float]:
    """Estrae un numero decimale da una stringa di prezzo."""
    if not text:
        return None
    # Rimuove simboli valuta e spazi, gestisce virgola decimale
    cleaned = re.sub(r"[^\d.,]", "", text)
    if not cleaned:
        return None
    # Gestisce formato italiano (1.234,56) e internazionale (1,234.56)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _normalize_selectors(selectors) -> list:
    """Normalizza i selettori in una lista di stringhe."""
    if not selectors:
        return []
    if isinstance(selectors, str):
        return [selectors]
    return [selector for selector in selectors if selector]


def _extract_price_from_soup(soup: BeautifulSoup, selectors) -> Optional[float]:
    """Prova più selettori fino a trovare un prezzo valido."""
    for selector in _normalize_selectors(selectors):
        element = soup.select_one(selector)
        if not element:
            continue
        price = _parse_price(element.get_text(" ", strip=True))
        if price is not None:
            return price
    return None


def _extract_prices_from_html_fallback(html: str) -> List[float]:
    """Cerca valori in euro direttamente nel markup come fallback.

    Supporta formati:
      - 649,00€  (€ dopo, virgola decimale)
      - €649,00  (€ prima, senza spazio)
      - € 649,00 (€ prima, con spazio)
      - 649.00€  (€ dopo, punto decimale)
      - €649.00  (€ prima, punto decimale)

    I prezzi vengono restituiti nell'ordine di apparizione nel markup.
    """
    # Un unico pattern che cattura sia € prima che € dopo il numero,
    # rispettando l'ordine di apparizione nel markup.
    pattern = (
        r"(?:€\s*(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{2})?)"
        r"|(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{2})?)\s*€)"
    )
    matches = re.findall(pattern, html, flags=re.IGNORECASE)

    prices = []
    for before, after in matches:
        match = before or after
        parsed = _parse_price(match)
        if parsed is not None:
            prices.append(parsed)
    return prices


def extract_price_data_from_html(html: str, price_selectors, original_price_selectors) -> Dict:
    """Estrae prezzo attuale e originale da una stringa HTML usando selettori con fallback."""
    soup = BeautifulSoup(html, "lxml")
    current_price = _extract_price_from_soup(soup, price_selectors)
    original_price = _extract_price_from_soup(soup, original_price_selectors)

    # Se il prezzo attuale non è stato trovato con i selettori, si può usare il
    # primo importo € presente nel markup come ultima risorsa.
    if current_price is None:
        fallback_prices = _extract_prices_from_html_fallback(html)
        if fallback_prices:
            current_price = fallback_prices[0]

    # IMPORTO ORIGINALE: NON viene mai dedotto dall'ordine di apparizione dei
    # prezzi nella pagina. Su pagine reali (Amazon, eBay) compaiono molti importi
    # € non correlati (risparmi, spedizione, articoli sponsorizzati, dati JS) in
    # ordine casuale: usare il "secondo prezzo" produce percentuali di sconto
    # sbagliate e notifiche false. Il prezzo di listino è affidabile solo se
    # trovato da un selettore dedicato (es. barrato / a-text-price).

    discount_percent = _calculate_discount(current_price, original_price)

    return {
        "current_price": current_price,
        "original_price": original_price,
        "discount_percent": discount_percent,
    }


def fetch_product_price(
    url: str,
    price_selector,
    original_price_selector,
    scraperapi_key: Optional[str] = None,
    timeout: int = 15,
) -> Dict:
    """Recupera prezzo attuale e prezzo originale da una pagina prodotto.

    Se ``scraperapi_key`` è fornita, le richieste passano dal proxy ScraperAPI
    (più affidabile contro i blocchi anti-bot); altrimenti si usa la richiesta
    diretta con User-Agent simulato.
    """
    response = None
    last_error = None
    max_retries = 3
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            if scraperapi_key:
                response = _get_via_scraperapi(url, scraperapi_key, timeout=timeout)
            else:
                response = requests.get(url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()
            break
        except requests.RequestException as e:
            last_error = e
            if attempt < max_retries - 1:
                delay = retry_delay * (2 ** attempt)  # Exponential backoff: 2s, 4s
                print(f"    ⚠️  Tentativo {attempt + 1} fallito, riprovo tra {delay}s...")
                time.sleep(delay)
                continue

    if response is None:
        return {"error": f"Errore di rete: {str(last_error)}"}

    price_selectors = _normalize_selectors(price_selector) + [
        "span.a-price-whole",
        "#corePriceDisplay_desktop_feature_div span.a-price-whole",
        "span.a-price > span:nth-child(2)",
        "span.a-price .a-offscreen",
    ]
    original_price_selectors = _normalize_selectors(original_price_selector) + [
        "span.a-text-price span.a-offscreen",
        "span.a-price.a-text-price span.a-offscreen",
        "#corePriceDisplay_desktop_feature_div span.a-text-price span.a-offscreen",
    ]

    data = extract_price_data_from_html(response.text, price_selectors, original_price_selectors)

    if data["current_price"] is None:
        if "continuare a fare acquisti" in response.text.lower() or "to discuss automated access" in response.text.lower():
            return {"error": "Amazon ha restituito una pagina di verifica/anti-bot; il prezzo non è disponibile via scraping."}
        return {"error": "Prezzo attuale non trovato con il selettore specificato"}

    return data


def _calculate_discount(current_price: Optional[float], original_price: Optional[float]) -> Optional[float]:
    """Calcola la percentuale di sconto.

    Restituisce None se:
      - current_price non è disponibile
      - original_price non è disponibile o è 0
      - current_price >= original_price (nessun sconto effettivo)
    """
    if current_price is None or not original_price or original_price <= 0:
        return None
    if current_price >= original_price:
        return None
    discount = ((original_price - current_price) / original_price) * 100
    return round(discount, 2)


def check_all_products(products: list, scraperapi_key: Optional[str] = None) -> list:
    """Controlla tutti i prodotti e restituisce quelli con sconto >= soglia.

    Se ``scraperapi_key`` è fornita, usa il proxy ScraperAPI per tutte le richieste.
    """
    results = []
    for product in products:
        print(f"  → Controllo: {product['name']}")
        data = fetch_product_price(
            product["url"],
            product.get("selector_price", "span.a-price-whole"),
            product.get("selector_original_price", "span.a-text-price span.a-offscreen"),
            scraperapi_key=scraperapi_key,
        )
        data["name"] = product["name"]
        data["url"] = product["url"]
        results.append(data)
        time.sleep(2)  # Rispetta i siti tra una richiesta e l'altra
    return results