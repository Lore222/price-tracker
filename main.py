import argparse
import datetime
import logging
import os
import sys
import time

from config_loader import load_config
from scraper import check_all_products
from state_store import DEFAULT_STATE_FILE, StateStore

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


def _filter_unnotified(state_store: StateStore, deals: list, min_improvement: float = 2.0) -> list:
    """Filtra le offerte già notificate e non migliorate.

    Un'offerta viene notificata se:
      - non è mai stata notificata per quell'URL, oppure
      - lo sconto è migliorato di almeno 'min_improvement' punti rispetto
        all'ultima notifica (così un prezzo che scende di nuovo provoca un
        nuovo alert invece di essere soppresso per sempre).

    Lo stato viene aggiornato e salvato su disco.
    """
    to_notify = []
    for deal in deals:
        url = deal.get("url")
        key = f"offer:{url}" if url else f"offer:{deal.get('name')}"
        prev = state_store.get(key)
        current = deal.get("discount_percent")
        if prev is None or (current is not None and (current - prev) >= min_improvement):
            to_notify.append(deal)
            if current is not None:
                state_store.set(key, current)
    if to_notify:
        state_store.save()
    return to_notify


def run_check(config):
    """Esegue un ciclo di controllo prezzi."""
    logger.info("=" * 60)
    logger.info("🔍 Controllo prezzi - %s", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    logger.info("=" * 60)

    results = check_all_products(
        config["products"],
        scraperapi_key=config.get("scraperapi_key"),
        cache_ttl_minutes=config.get("price_cache_minutes", 60),
    )

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
        state_store = StateStore(os.getenv("PRICE_STATE_FILE", DEFAULT_STATE_FILE))
        deals_to_notify = _filter_unnotified(state_store, deals)
        if deals_to_notify:
            logger.info("🎯 Trovate %d nuove offerte con sconto ≥ %s%%!",
                        len(deals_to_notify), threshold)
            from telegram_notifier import send_telegram_alert
            send_telegram_alert(config, deals_to_notify)
        else:
            logger.info("😴 Offerte già notificate e invariate: nessun nuovo alert.")
    else:
        logger.info("😴 Nessuna offerta con sconto ≥ %s%% in questo momento.", threshold)


def run_summary(config):
    """Esegue un riepilogo prezzi e invia un messaggio Telegram serale."""
    logger.info("📊 Eseguo il riepilogo prezzi serale - %s", datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    results = check_all_products(
        config["products"],
        scraperapi_key=config.get("scraperapi_key"),
        cache_ttl_minutes=config.get("price_cache_minutes", 60),
    )
    from telegram_notifier import send_telegram_summary
    send_telegram_summary(config, results)


def should_run_continuously(args, env):
    """Restituisce True se si vuole eseguire in modalità loop continuo."""
    if args is not None and getattr(args, "loop", False):
        return True
    return str(env.get("CONTINUOUS_MODE", "")).lower() in {"1", "true", "yes", "on"}


def parse_args():
    parser = argparse.ArgumentParser(description="Price Tracker")
    parser.add_argument("--loop", action="store_true", help="Esegue il monitoraggio in loop continuo")
    parser.add_argument("--summary", action="store_true", help="Esegue solo il riepilogo prezzi serale")
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        config = load_config()
    except (FileNotFoundError, ValueError) as e:
        logger.error("❌ Errore configurazione: %s", e)
        sys.exit(1)

    # Modalità riepilogo serale: esegue solo il riepilogo e termina
    if args.summary:
        run_summary(config)
        return

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

    try:
        import schedule
    except ModuleNotFoundError:
        logger.error(
            "❌ Dipendenza mancante: 'schedule'. Installa le dipendenze con 'pip install -r requirements.txt'"
        )
        sys.exit(1)

    schedule.every(interval).minutes.do(run_check, config)
    schedule.every().day.at("20:00").do(run_summary, config)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("👋 Monitoraggio fermato.")


if __name__ == "__main__":
    main()