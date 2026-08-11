import argparse
import datetime
import logging
import os
import sys
import time

import schedule

from config_loader import load_config
from telegram_notifier import send_telegram_alert
from scraper import check_all_products

# Configurazione logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%d/%m/%Y %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("price_tracker.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def run_check(config):
    """Esegue un ciclo di controllo prezzi."""
    logger.info("=" * 60)
    logger.info("🔍 Controllo prezzi - %s", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logger.info("=" * 60)

    results = check_all_products(config["products"])

    # Filtra le offerte con sconto >= soglia
    threshold = config["discount_threshold"]
    deals = [
        r for r in results
        if not r.get("error")
        and r.get("discount_percent") is not None
        and r["discount_percent"] >= threshold
    ]

    # Mostra riepilogo
    for r in results:
        if r.get("error"):
            logger.warning("⚠️  %s: %s", r["name"], r["error"])
        else:
            discount = r.get("discount_percent")
            if discount is not None:
                logger.info("📦 %s: €%s (originale €%s) - Sconto %s%%",
                            r["name"], r["current_price"], r["original_price"], discount)
            else:
                logger.info("📦 %s: €%s (prezzo originale non disponibile)",
                            r["name"], r["current_price"])

    if deals:
        logger.info("🎯 Trovate %d offerte con sconto ≥ %s%%!", len(deals), threshold)
        send_telegram_alert(config, deals)
    else:
        logger.info("😴 Nessuna offerta con sconto ≥ %s%% in questo momento.", threshold)


def should_run_continuously(args, env):
    """Restituisce True se si vuole eseguire in modalità loop continuo."""
    if args is not None and getattr(args, "loop", False):
        return True
    return str(env.get("CONTINUOUS_MODE", "")).lower() in {"1", "true", "yes", "on"}


def parse_args():
    parser = argparse.ArgumentParser(description="Price Tracker")
    parser.add_argument("--loop", action="store_true", help="Esegue il monitoraggio in loop continuo")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        logger.error("❌ Errore configurazione: %s", e)
        sys.exit(1)

    interval = config["check_interval_minutes"]
    continuous = should_run_continuously(args, os.environ)

    logger.info("🚀 Avvio monitoraggio prezzi")
    logger.info("   Modalità: %s", "loop continuo" if continuous else "esecuzione singola")
    logger.info("   Intervallo: ogni %d minuti", interval)
    logger.info("   Soglia sconto: %s%%", config["discount_threshold"])
    logger.info("   Prodotti monitorati: %d", len(config["products"]))
    if continuous:
        logger.info("   Premi Ctrl+C per fermare\n")
    else:
        logger.info("")

    run_check(config)

    if not continuous:
        logger.info("✅ Esecuzione singola completata.")
        return

    schedule.every(interval).minutes.do(run_check, config)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("👋 Monitoraggio fermato.")


if __name__ == "__main__":
    main()