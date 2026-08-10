import json
import os
from typing import Dict, Any, Optional


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
    email_env = {
        "smtp_server": os.getenv("SMTP_SERVER"),
        "smtp_port": _safe_int_env("SMTP_PORT", 587),
        "smtp_port_ssl": _safe_int_env("SMTP_PORT_SSL", 465),
        "smtp_port_plain": _safe_int_env("SMTP_PORT_PLAIN", 25),
        "sender_email": os.getenv("SENDER_EMAIL"),
        "sender_password": os.getenv("SENDER_PASSWORD"),
        "recipient_email": os.getenv("RECIPIENT_EMAIL"),
    }

    if not any(email_env.values()):
        return {}

    return {"email": email_env}


def _validate_email_config(email_config: Dict[str, Any]) -> None:
    """Valida che la configurazione email abbia tutti i campi obbligatori."""
    required_fields = {
        "smtp_server": "server SMTP",
        "sender_email": "email mittente",
        "sender_password": "password mittente",
        "recipient_email": "email destinatario",
    }
    missing = []
    for field, label in required_fields.items():
        if not email_config.get(field):
            missing.append(label)

    if missing:
        raise ValueError(f"Configurazione email incompleta: mancano i seguenti campi: {', '.join(missing)}")


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """Carica e valida la configurazione, usando valori di default o variabili d'ambiente."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
    else:
        config = {
            "email": {},
            "check_interval_minutes": 60,
            "discount_threshold": 70,
            "products": [],
        }

    env_config = _get_env_config()
    if env_config:
        config.setdefault("email", {})
        config["email"].update({k: v for k, v in env_config["email"].items() if v is not None})

    interval = os.getenv("CHECK_INTERVAL_MINUTES")
    if interval is not None:
        config["check_interval_minutes"] = _safe_int_env("CHECK_INTERVAL_MINUTES", 60)

    threshold = os.getenv("DISCOUNT_THRESHOLD")
    if threshold is not None:
        config["discount_threshold"] = _safe_float_env("DISCOUNT_THRESHOLD", 70.0)

    config.setdefault("email", {})
    config.setdefault("check_interval_minutes", 60)
    config.setdefault("discount_threshold", 70)
    config.setdefault("products", [])

    if not isinstance(config["products"], list):
        raise ValueError("La lista 'products' deve essere una lista")

    for product in config["products"]:
        if "name" not in product or "url" not in product:
            raise ValueError("Ogni prodotto deve avere 'name' e 'url'")

    # Valida email solo se ci sono prodotti configurati (se non ci sono prodotti, non serve email)
    if config["products"]:
        _validate_email_config(config["email"])

    return config