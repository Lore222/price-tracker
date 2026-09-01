import html
import logging
import requests
from typing import Dict, List

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"

logger = logging.getLogger(__name__)


def _escape_text(value) -> str:
    return html.escape(str(value), quote=True)


def _format_price(value) -> str:
    """Formatta un prezzo in stile italiano (es. 1.234,56).

    Restituisce 'N/D' quando il valore non è disponibile (None), così da non
    comparire mai nei messaggi come '€None'.
    """
    if value is None:
        return "N/D"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    integer, decimal = f"{num:.2f}".split(".")
    return f"{int(integer):,}".replace(",", ".") + "," + decimal


def _format_percent(value) -> str:
    """Formatta una percentuale in stile italiano (es. 13,35% -> 13,35)."""
    if value is None:
        return "N/D"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{num:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _send_telegram_message(config: Dict, text: str) -> bool:
    """Invia un messaggio Telegram generico a uno o più chat_id (separati da virgola)."""
    telegram_config = config["telegram"]
    bot_token = telegram_config.get("bot_token")
    chat_ids_raw = telegram_config.get("chat_id")

    if not bot_token or not chat_ids_raw:
        logger.error("Configurazione Telegram incompleta: mancano bot_token o chat_id")
        return False

    # Supporta più destinatari separati da virgola, es. "169943050,761389545"
    chat_ids = [c.strip() for c in str(chat_ids_raw).split(",") if c.strip()]
    if not chat_ids:
        logger.error("Configurazione Telegram incompleta: chat_id vuoto")
        return False

    url = TELEGRAM_API.format(token=bot_token)
    all_ok = True
    for chat_id in chat_ids:
        try:
            response = requests.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                },
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            if data.get("ok"):
                logger.info("Messaggio Telegram inviato a %s", chat_id)
            else:
                logger.error("Errore invio Telegram a %s: %s", chat_id, data)
                all_ok = False
        except Exception as e:
            logger.exception("Errore invio Telegram a %s: %s", chat_id, e)
            all_ok = False
    return all_ok


def _build_deals_message(config: Dict, deals: List[Dict]) -> str:
    """Costruisce il testo del messaggio Telegram con le offerte trovate."""
    lines = [
        "🔥 <b>OFFERTE IMPERDIBILI!</b>",
        f"Trovate <b>{len(deals)}</b> offerte con sconto ≥ {_format_percent(config['discount_threshold'])}%",
        "─────────────────────────",
    ]

    for deal in deals:
        discount = _format_percent(deal.get("discount_percent"))
        name = _escape_text(deal.get("name", "N/D"))
        current = _format_price(deal.get("current_price"))
        original = _format_price(deal.get("original_price"))
        url = _escape_text(deal.get("url", ""))

        lines.append(f"📦 <b>{name}</b>")
        if original != "N/D":
            lines.append(f"💶 Prezzo: <s>€{_escape_text(original)}</s> → <b>€{_escape_text(current)}</b>")
        else:
            lines.append(f"💶 Prezzo attuale: <b>€{_escape_text(current)}</b>")
        lines.append(f"🏷️ Sconto: <b>{_escape_text(discount)}%</b>")
        lines.append(f"🔗 <a href=\"{url}\">Vai all'offerta</a>")
        lines.append("─────────────────────────")

    lines.append("Monitoraggio prezzi automatico")
    return "\n".join(lines)


def _build_summary_message(config: Dict, products: List[Dict]) -> str:
    """Costruisce il testo del riepilogo prezzi serale."""
    lines = [
        "🗓️ <b>RIEPILOGO PREZZI SERALI</b>",
        f"Prodotti monitorati: <b>{len(products)}</b>",
        "─────────────────────────",
    ]

    for item in products:
        name = _escape_text(item.get("name", "N/D"))
        url = _escape_text(item.get("url", ""))
        lines.append(f"📦 <b>{name}</b>")

        if item.get("error"):
            lines.append(f"❌ Errore: {_escape_text(item['error'])}")
        else:
            current = _format_price(item.get("current_price"))
            original = _format_price(item.get("original_price"))
            discount = _format_percent(item.get("discount_percent"))
            discount_text = f" - <b>{_escape_text(discount)}%</b>" if discount != "N/D" else ""
            lines.append(f"💶 Prezzo attuale: <b>€{_escape_text(current)}</b>")
            if original != "N/D":
                lines.append(f"💸 Prezzo originale: €{_escape_text(original)}{discount_text}")
            else:
                lines.append(f"💸 Prezzo originale: non disponibile{discount_text}")

        lines.append(f"🔗 <a href=\"{url}\">Vai al prodotto</a>")
        lines.append("─────────────────────────")

    lines.append("Monitoraggio prezzi automatico")
    return "\n".join(lines)


def send_telegram_alert(config: Dict, deals: List[Dict]) -> bool:
    """Invia un messaggio Telegram con le offerte trovate."""
    if not deals:
        return False

    message = _build_deals_message(config, deals)
    return _send_telegram_message(config, message)


def send_telegram_summary(config: Dict, products: List[Dict]) -> bool:
    """Invia un riepilogo Telegram di tutti i prezzi dei prodotti."""
    if not products:
        return False

    message = _build_summary_message(config, products)
    return _send_telegram_message(config, message)
