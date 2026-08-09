import json
import os
from typing import Dict, Any


def _get_env_config() -> Dict[str, Any]:
    """Restituisce una configurazione minima dai valori d'ambiente, se presenti."""
    email_env = {
        "smtp_server": os.getenv("SMTP_SERVER"),
        "smtp_port": int(os.getenv("SMTP_PORT", 587)) if os.getenv("SMTP_PORT") else 587,
        "smtp_port_ssl": int(os.getenv("SMTP_PORT_SSL", 465)) if os.getenv("SMTP_PORT_SSL") else 465,
        "smtp_port_plain": int(os.getenv("SMTP_PORT_PLAIN", 25)) if os.getenv("SMTP_PORT_PLAIN") else 25,
        "sender_email": os.getenv("SENDER_EMAIL"),
        "sender_password": os.getenv("SENDER_PASSWORD"),
        "recipient_email": os.getenv("RECIPIENT_EMAIL"),
    }

    if not any(email_env.values()):
        return {}

    return {"email": email_env}


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
    if interval:
        config["check_interval_minutes"] = int(interval)

    threshold = os.getenv("DISCOUNT_THRESHOLD")
    if threshold:
        config["discount_threshold"] = float(threshold)

    config.setdefault("email", {})
    config.setdefault("check_interval_minutes", 60)
    config.setdefault("discount_threshold", 70)
    config.setdefault("products", [])

    if not isinstance(config["products"], list):
        raise ValueError("La lista 'products' deve essere una lista")

    for product in config["products"]:
        if "name" not in product or "url" not in product:
            raise ValueError("Ogni prodotto deve avere 'name' e 'url'")

    return config