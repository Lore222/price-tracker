# 🛒 Price Tracker - Monitoraggio Offerte E-commerce

Programma Python che monitora i prezzi su vari siti e-commerce e invia messaggi Telegram:
- **Alert periodico (3 volte al giorno, fascia diurna)**: quando trova prodotti con sconto superiore alla soglia configurata
- **Riepilogo giornaliero alle 20:00**: resoconto di tutti i prezzi, anche se nessun prodotto ha raggiunto lo sconto desiderato

## ✨ Funzionalità

- 🔍 Controllo automatico dei prezzi 3 volte al giorno (9, 15, 21 UTC), con sospensione notturna
- 📨 Invio messaggi Telegram con le offerte trovate (solo se sconto ≥ soglia)
- 🗓️ Riepilogo prezzi giornaliero alle 20:00 via GitHub Actions (sempre inviato)
- 🎯 Soglia sconto configurabile (default: 70%)
- 🌐 Supporto multi-sito (Amazon, eBay, e altri)
- 📊 Calcolo automatico della percentuale di sconto
- 🛡️ Gestione errori di rete e parsing
- 🤖 Automazione completa con GitHub Actions (nessun processo locale necessario)

## 📋 Requisiti

- Python 3.8+
- Un bot Telegram con il suo token e un chat ID (vedi sotto)
- (Opzionale) Un repository GitHub per l'automazione con GitHub Actions

## 🚀 Installazione

```bash
cd price-tracker
pip install -r requirements.txt
```

## ⚙️ Configurazione

### 1. Configurare Telegram (config.json)

Per ricevere gli alert su Telegram devi creare un bot e ottenere il tuo chat ID:

1. Su Telegram apri il canale con **@BotFather** e usa il comando `/newbot` per creare il bot
2. BotFather ti fornirà un **bot token** (formato `123456789:AA...`)
3. Avvia una conversazione con il tuo bot e inviagli un messaggio
4. Ottieni il tuo **chat ID** (puoi usare ad esempio l'endpoint `getUpdates` dell'API)

Inserisci i dati nel campo `telegram` del file `config.json`:

```json
"telegram": {
    "bot_token": "123456789:AAEsempioTokenDelBot",
    "chat_id": "123456789"
}
```

> 💡 Puoi inviare le notifiche a **più chat** separando i chat ID con una virgola, ad esempio `"chat_id": "123456789,987654321"`.

> 💡 In alternativa puoi impostarli tramite le variabili d'ambiente `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`, che hanno la precedenza sui valori del file.

### 2. Aggiungere i prodotti da monitorare

Nel campo `products` aggiungi ogni prodotto con:
- `name`: nome descrittivo
- `url`: URL della pagina prodotto
- `selector_price`: selettore CSS del prezzo attuale
- `selector_original_price`: selettore CSS del prezzo originale (barrato)

**Esempio per Amazon:**
```json
{
    "name": "iPhone 15",
    "url": "https://www.amazon.it/dp/B0CHX2F5QT",
    "selector_price": "span.a-price-whole",
    "selector_original_price": "span.a-text-price span.a-offscreen"
}
```

**Esempio per eBay:**
```json
{
    "name": "PlayStation 5",
    "url": "https://www.ebay.it/itm/ESEMPIO_ID",
    "selector_price": "span.ux-textspans--BOLD",
    "selector_original_price": "span.ux-textspans--STRIKETHROUGH"
}
```

> 💡 **Trovare i selettori CSS**: apri la pagina prodotto, fai clic destro sul prezzo → "Ispeziona", e copia il selettore dell'elemento.

### 3. (Opzionale) Rendere lo scraping più affidabile con ScraperAPI

Alcuni siti (in particolare Amazon) mostrano pagine di verifica anti-bot che bloccano
lo scraping diretto. Per ridurre questi errori puoi usare **[ScraperAPI](https://scraperapi.com)**
come proxy dedicato. Lo scraper la userà automaticamente se trova una chiave.

Impostala via **variabile d'ambiente** (consigliato, non viene mai committato nel repo):

```bash
export SCRAPERAPI_API_KEY="la_tua_chiave"
```

In alternativa puoi inserirla nella sezione `scraperapi` del `config.json`:

```json
"scraperapi": {
    "api_key": "la_tua_chiave"
}
```

> ⚠️ **Importante**: `config.json` ora è tracciato sul repository. Per non esporre la
chiave pubblicamente, usa la variabile d'ambiente o un **GitHub secret**
(`SCRAPERAPI_API_KEY`) nei workflow. La chiave via `config.json` va bene solo in locale.

### 4. Impostazioni personalizzate

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `check_interval_minutes` | Intervallo controlli in minuti | 60 |
| `discount_threshold` | Soglia sconto per alert (%) | 70 |

## ▶️ Utilizzo

### Esecuzione locale

```bash
# Controllo singolo
python main.py

# Monitoraggio continuo (controlli periodici + riepilogo alle 20:00)
python main.py --loop

# Solo riepilogo serale (invia il resoconto e termina)
python main.py --summary
```

### Automazione con GitHub Actions (consigliata)

Il progetto include due workflow GitHub Actions che funzionano senza bisogno di tenere il computer acceso:

| Workflow | Schedule | Funzione |
|----------|----------|----------|
| `Price Tracker` | 3×/giorno (9, 15, 21 UTC, fascia diurna) | Controlla i prezzi e invia alert Telegram solo se sconto ≥ soglia |
| `Daily Price Summary` | Ogni giorno alle 20:00 (18:00 UTC) | Invia il riepilogo di tutti i prezzi, anche senza sconto |

**Setup su GitHub:**
1. Crea un repository su GitHub e pusha il progetto
2. Aggiungi i secrets del repository:
   - `TELEGRAM_BOT_TOKEN` → il token del tuo bot
   - `TELEGRAM_CHAT_ID` → il tuo chat ID (più chat ID separati da virgola)
   - `SCRAPERAPI_API_KEY` → (opzionale) la tua chiave ScraperAPI per uno scraping più affidabile
3. I workflow si attivano automaticamente

> ⚠️ **Nota**: su GitHub Actions la configurazione viene letta dalle variabili d'ambiente (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SCRAPERAPI_API_KEY`), non dal file `config.json`. I prodotti da monitorare vanno configurati nel file `config.json` presente nel repository.

## 📁 Struttura del progetto

```
price-tracker/
├── main.py                    # Punto di ingresso con scheduler
├── config.json                # Configurazione Telegram e prodotti
├── config_loader.py           # Caricamento e validazione configurazione
├── scraper.py                 # Estrazione prezzi dai siti
├── telegram_notifier.py       # Invio messaggi Telegram di alert e riepilogo
├── requirements.txt           # Dipendenze Python
└── .github/workflows/
    ├── price-tracker.yml      # Workflow orario (alert sconti)
    └── daily-summary.yml      # Workflow giornaliero alle 20:00 (riepilogo)
```

## ⚠️ Note importanti

- **Rispetta i siti web**: il programma attende 2 secondi tra una richiesta e l'altra
- **Selettori CSS**: possono cambiare se il sito aggiorna il layout, aggiorna i selettori in `config.json`
- **Anti-bot**: alcuni siti potrebbero bloccare lo scraping, in tal caso usa un User-Agent diverso o un proxy
- **Telegram**: il bot token è un segreto, non condividerlo pubblicamente. Il file `config.json` è tracciato sul repository: non inserire al suo interno token o chiavi API, usa le variabili d'ambiente o i GitHub secrets
- **GitHub Actions**: i cron job usano il fuso orario UTC. Il riepilogo delle 20:00 italiane corrisponde a `0 18 * * *` (18:00 UTC). In estate (CEST) l'Italia è UTC+2, in inverno (CET) UTC+1 — regola il cron se necessario.

## 💳 Consumo crediti ScraperAPI (piano gratuito: 1000/mese)

Ogni run consuma **1 credito per ogni prodotto** in `config.json` (8 con la configurazione di default). Con la schedule corrente:

| Voce | Run/giorno | Crediti/giorno |
|------|------------|----------------|
| `Price Tracker` (9, 15, 21 UTC) | 3 | 3 × 8 = 24 |
| `Daily Price Summary` (18 UTC) | 1 | 8 |
| **Totale** | | **~32/giorno** |

→ **~32 × 30 = ~960 crediti/mese**, dentro i 1000 ma con poco margine.

> 💡 Se hai bisogno di più respiro, riduci il numero di prodotti: ogni prodotto tolto risparmia 4 crediti/giorno (3 controlli + 1 riepilogo), cioè ~120/mese.

## 🔒 Privacy

- Il bot token Telegram non va salvato in `config.json` (tracciato sul repository): usa le variabili d'ambiente o i GitHub secrets
- Su GitHub Actions il token è salvato come secret del repository (mai esposto nei log)
- Se configuri una chiave ScraperAPI, le richieste passano dal proxy di ScraperAPI (servizio di terze parti) per evitare blocchi anti-bot; senza chiave le richieste vanno direttamente ai siti e-commerce configurati
