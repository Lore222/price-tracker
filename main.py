import argparse
import datetime
import os
import sys
import time

import schedule

from config_loader import load_config
from email_notifier import send_alert_email
from scraper import check_all_products


def run_check(config):
    """Esegue un ciclo di controllo prezzi."""
    print(f"\n{'='*60}")
    print(f"🔍 Controllo prezzi - {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"{'='*60}")

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
            print(f"  ⚠️  {r['name']}: {r['error']}")
        else:
            discount = r.get("discount_percent")
            if discount is not None:
                print(f"  📦 {r['name']}: €{r['current_price']} "
                      f"(originale €{r['original_price']}) - Sconto {discount}%")
            else:
                print(f"  📦 {r['name']}: €{r['current_price']} (prezzo originale non disponibile)")

    if deals:
        print(f"\n  🎯 Trovate {len(deals)} offerte con sconto ≥ {threshold}%!")
        send_alert_email(config, deals)
    else:
        print(f"\n  😴 Nessuna offerta con sconto ≥ {threshold}% in questo momento.")


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
        print(f"❌ Errore configurazione: {e}")
        sys.exit(1)

    interval = config["check_interval_minutes"]
    continuous = should_run_continuously(args, os.environ)

    print(f"🚀 Avvio monitoraggio prezzi")
    print(f"   Modalità: {'loop continuo' if continuous else 'esecuzione singola'}")
    print(f"   Intervallo: ogni {interval} minuti")
    print(f"   Soglia sconto: {config['discount_threshold']}%")
    print(f"   Prodotti monitorati: {len(config['products'])}")
    if continuous:
        print(f"   Premi Ctrl+C per fermare\n")
    else:
        print()

    run_check(config)

    if not continuous:
        print("\n✅ Esecuzione singola completata.")
        return

    schedule.every(interval).minutes.do(run_check, config)

    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Monitoraggio fermato.")


if __name__ == "__main__":
    main()