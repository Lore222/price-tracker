import json
import os
from typing import Dict, Any


def _safe_int_env(var_name: str, default: int) -> int:
    """Legge una variabile d'ambiente come intero, con fallback sicuro."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(f"La variabile d'ambiente {var_name} deve essere un numero intero, ricevuto: '{value}'")


def _safe_float_env(var_name: str, default: float) -> float:
    """Legge una variabile d'ambiente come float, con fallback sicuro."""
    value = os.getenv(var_name)
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(f"La variabile d'ambiente {var_name} deve essere un numero decimale, ricevuto: '{value}'")


def _get_env_config() -> Dict[str, Any]:
    """Restituisce una configurazione minima dai valori d'ambiente, se presenti."""
    telegram_env = {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
    }

    if not any(telegram_env.values()):
        return {}

    return {"telegram": telegram_env}


def _validate_telegram_config(telegram_config: Dict[str, Any]) -> None:
    """Valida che la configurazione Telegram abbia i campi obbligatori."""
    required_fields = {
        "bot_token": "bot token",
        "chat_id": "chat id",
    }
    missing = []
    for field, label in required_fields.items():
        if not telegram_config.get(field):
            missing.append(label)

    if missing:
        raise ValueError(f"Configurazione Telegram incompleta: mancano i seguenti campi: {', '.join(missing)}")


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Carica e valida la configurazione, usando valori di default o variabili d'ambiente."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {
            "telegram": {},
            "check_interval_minutes": 60,
            "discount_threshold": 70,
            "products": [],
        }

    env_config = _get_env_config()
    if env_config:
        config.setdefault("telegram", {})
        config["telegram"].update({k: v for k, v in env_config["telegram"].items() if v is not None})

    interval = os.getenv("CHECK_INTERVAL_MINUTES")
    if interval is not None:
        config["check_interval_minutes"] = _safe_int_env("CHECK_INTERVAL_MINUTES", 60)

    threshold = os.getenv("DISCOUNT_THRESHOLD")
    if threshold is not None:
        config["discount_threshold"] = _safe_float_env("DISCOUNT_THRESHOLD", 70.0)

    cache_minutes = os.getenv("PRICE_CACHE_MINUTES")
    if cache_minutes is not None:
        config["price_cache_minutes"] = _safe_int_env("PRICE_CACHE_MINUTES", 60)

    config.setdefault("telegram", {})
    config.setdefault("check_interval_minutes", 60)
    config.setdefault("discount_threshold", 70)
    config.setdefault("price_cache_minutes", 60)
    config.setdefault("products", [])

    # Chiave API ScraperAPI (opzionale). Priorità alla variabile d'ambiente
    # SCRAPERAPI_API_KEY (mai committata), fallback alla sezione "scraperapi"
    # del file di configurazione. Usata per fare lo scraping via proxy e
    # ridurre i blocchi anti-bot.
    scraperapi_env = os.getenv("SCRAPERAPI_API_KEY")
    scraperapi_section = config.get("scraperapi") or {}
    config["scraperapi_key"] = scraperapi_env or scraperapi_section.get("api_key")

    if not isinstance(config["products"], list):
        raise ValueError("La lista 'products' deve essere una lista")

    for product in config["products"]:
        if "name" not in product or "url" not in product:
            raise ValueError("Ogni prodotto deve avere 'name' e 'url'")

    # Valida Telegram solo se ci sono prodotti configurati (se non ci sono prodotti, non serve notificare)
    if config["products"]:
        _validate_telegram_config(config["telegram"])

    return config