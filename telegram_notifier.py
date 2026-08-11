import requests
from typing import Dict, List

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def _build_message(config: Dict, deals: List[Dict]) -> str:
    """Costruisce il testo del messaggio Telegram con le offerte trovate."""
    lines = [
        "🔥 <b>OFFERTE IMPERDIBILI!</b>",
        f"Trovate <b>{len(deals)}</b> offerte con sconto ≥ {config['discount_threshold']}%",
        "─────────────────────────",
    ]

    for deal in deals:
        discount = deal.get("discount_percent", 0)
        current = deal.get("current_price", "N/D")
        original = deal.get("original_price", "N/D")
        lines.append(f"📦 <b>{deal['name']}</b>")
        lines.append(f"💶 Prezzo: <s>€{original}</s> → <b>€{current}</b>")
        lines.append(f"🏷️ Sconto: <b>{discount}%</b>")
        lines.append(f"🔗 <a href=\"{deal['url']}\">Vai all'offerta</a>")
        lines.append("─────────────────────────")

    lines.append("Monitoraggio prezzi automatico")
    return "\n".join(lines)


def send_telegram_alert(config: Dict, deals: List[Dict]) -> bool:
    """Invia un messaggio Telegram con le offerte trovate."""
    if not deals:
        return False

    telegram_config = config["telegram"]
    bot_token = telegram_config.get("bot_token")
    chat_id = telegram_config.get("chat_id")

    if not bot_token or not chat_id:
        print("  ❌ Configurazione Telegram incompleta: mancano bot_token o chat_id")
        return False

    message = _build_message(config, deals)
    url = TELEGRAM_API.format(token=bot_token)

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            print(f"  ✅ Messaggio Telegram inviato con {len(deals)} offerte")
            return True
        print(f"  ❌ Errore invio Telegram: {data}")
        return False
    except Exception as e:
        print(f"  ❌ Errore invio Telegram: {e}")
        return False