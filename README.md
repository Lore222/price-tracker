# 🛒 Price Tracker - Monitoraggio Offerte E-commerce

Programma Python che monitora i prezzi su vari siti e-commerce e invia messaggi Telegram:
- **Alert periodici**: in locale con l'intervallo configurato; su GitHub Actions, una run ogni due giorni
- **Riepilogo giornaliero**: alle 20:00 in modalità `--loop`; il workflow GitHub Actions è disponibile solo su avvio manuale

## ✨ Funzionalità

- 🔍 Controllo automatico dei prezzi; su GitHub Actions una run ogni due giorni alle 12 UTC
- 📨 Invio messaggi Telegram con le offerte trovate (solo se sconto ≥ soglia)
- 🗓️ Riepilogo prezzi alle 20:00 nel loop locale; il workflow GitHub Actions è manuale e non schedulato
- 🎯 Soglia sconto configurabile (default: 70%)
- 🔁 Deduplicazione degli alert durante le esecuzioni che condividono `state.json`; la persistenza dello stato tra run GitHub Actions non è attualmente garantita dal workflow.
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
| `check_interval_minutes` | Intervallo controlli in minuti (modalità `--loop` locale) | 60 |
| `price_cache_minutes` | Durata cache prezzi in minuti: entro questo tempo non rifà la chiamata API per lo stesso prodotto | 60 |
| `discount_threshold` | Soglia sconto per alert (%) | 70 |

> 💡 I valori numerici possono essere scritti come numeri o come stringhe numeriche
> (es. `"60"`) e vengono convertiti automaticamente. Range validi:
> `check_interval_minutes` ≥ 1, `price_cache_minutes` ≥ 0 (0 = cache disattivata),
> `discount_threshold` tra 0 e 100. Un valore non valido viene segnalato subito
> all'avvio con un messaggio chiaro, invece di far crashare il programma a metà esecuzione.

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

| Workflow | Schedule (cron UTC) | Orari Italia | Funzione |
|----------|----------|----------|----------|
| `Price Tracker` | ogni due giorni: `0 12 */2 * *` | 13:00 CET / 14:00 CEST | Controlla i prezzi e invia alert Telegram solo se sconto ≥ soglia |
| `Daily Price Summary` | manuale (`workflow_dispatch`) | – | Riepilogo di tutti i prezzi, anche senza sconto |

> 💳 La cadenza è ridotta per rispettare il limite ScraperAPI di 1000 crediti per periodo, che si azzera il giorno 13. Il cron `*/2` esegue nei giorni dispari del mese; la distanza tra run può quindi variare al cambio del mese.
>
> 🌙 **Sospensione notturna**: i controlli sono in fascia diurna e non vengono eseguiti nella notte italiana (00:00–08:00).
>
> 🛡️ **Concurrency guard**: impedisce run simultanee dello stesso workflow, ma una run annullata può aver già consumato crediti. Anche le esecuzioni manuali e i retry consumano crediti.

**Setup su GitHub:**
1. Crea un repository su GitHub e pusha il progetto
2. Aggiungi i secrets del repository:
   - `TELEGRAM_BOT_TOKEN` → il token del tuo bot
   - `TELEGRAM_CHAT_ID` → il tuo chat ID (più chat ID separati da virgola)
   - `SCRAPERAPI_API_KEY` → (opzionale) la tua chiave ScraperAPI per uno scraping più affidabile
3. `Price Tracker` si attiva secondo la schedulazione; `Daily Price Summary` è avviabile manualmente

> ⚠️ **Nota**: su GitHub Actions la configurazione viene letta dalle variabili d'ambiente (`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `SCRAPERAPI_API_KEY`), non dal file `config.json`. I prodotti da monitorare vanno configurati nel file `config.json` presente nel repository.

## 📁 Struttura del progetto

```
price-tracker/
├── main.py                    # Punto di ingresso con scheduler + dedup alert
├── config.json                # Configurazione Telegram e prodotti
├── config_loader.py           # Caricamento e validazione configurazione
├── scraper.py                 # Estrazione prezzi dai siti
├── telegram_notifier.py       # Invio messaggi Telegram di alert e riepilogo
├── state_store.py             # Persistenza stato (dedup notifiche) in state.json
├── requirements.txt           # Dipendenze Python
└── .github/workflows/
    ├── price-tracker.yml      # Workflow ogni due giorni (alert sconti)
    └── daily-summary.yml      # Riepilogo manuale, non schedulato
```

## ⚠️ Note importanti

- **Rispetta i siti web**: il programma attende 2 secondi tra una richiesta e l'altra
- **Selettori CSS**: possono cambiare se il sito aggiorna il layout, aggiorna i selettori in `config.json`
- **Anti-bot**: alcuni siti potrebbero bloccare lo scraping, in tal caso usa un User-Agent diverso o un proxy
- **Telegram**: il bot token è un segreto, non condividerlo pubblicamente. Il file `config.json` è tracciato sul repository: non inserire al suo interno token o chiavi API, usa le variabili d'ambiente o i GitHub secrets
- **GitHub Actions**: i cron job usano il fuso orario UTC. Il controllo alle 12 UTC corrisponde alle 13:00 italiane in inverno (CET) e alle 14:00 in estate (CEST).

## 💳 Consumo crediti ScraperAPI (piano: 1000/mese)

> ⚠️ **Costi reali misurati** (report ScraperAPI, ottobre 2026): la verifica `credit_cost = (successful + cancelled) × 5` torna **esatta** per ogni giorno.
>
> | Dominio | Costo per richiesta |
> |---|---|
> | **amazon.it** | **5 crediti** (categoria E-Commerce con scraping dedicato) |
> | **ebay.it** | **1 credito** |
>
> ⚠️ Le richieste **cancelled** (il client si disconnette per timeout) vengono **comunque addebitate**: 5 crediti su Amazon e 1 su eBay. Ogni retry successivo costa altrettanto. Nel solo ottobre 2026 i cancelled sono stati 27 → **135 crediti sprecati** (16% del totale).
>
> Per questo il codice usa **timeout 40s** (non 15) e **max 2 tentativi**: con 15s le pagine lente di Amazon producevano fino a 15 cancelled al giorno, ognuno dei quali pagava due volte (timeout + retry).

I 6 prodotti attualmente in `config.json` puntano tutti ad Amazon: una run costa quindi circa **30 crediti** senza retry. Con `0 12 */2 * *` si effettuano circa 15 run in 30 giorni o 16 in 31 giorni: circa **450–480 crediti**, lasciando margine per i retry. Le esecuzioni manuali e le richieste annullate possono aumentare il consumo; controlla il contatore ScraperAPI e mantieni il riepilogo automatico disattivato.

> 💡 Per ridurre ulteriormente i consumi, diminuisci il numero di prodotti monitorati o aumenta l'intervallo tra le run.

## 🔒 Privacy

- Il bot token Telegram non va salvato in `config.json` (tracciato sul repository): usa le variabili d'ambiente o i GitHub secrets
- Su GitHub Actions il token è salvato come secret del repository (mai esposto nei log)
- Se configuri una chiave ScraperAPI, le richieste passano dal proxy di ScraperAPI (servizio di terze parti) per evitare blocchi anti-bot; senza chiave le richieste vanno direttamente ai siti e-commerce configurati
- I segreti (bot token Telegram, chiave ScraperAPI) vengono **rimossi automaticamente** (`***`) dai log e dai messaggi di errore: le eccezioni di `requests` includono l'URL completo della richiesta e, senza questa redazione, token e chiave finirebbero in `price_tracker.log`, nei log di GitHub Actions e nei messaggi Telegram
- I workflow GitHub Actions usano **permessi minimi** (`contents: read`, più `actions: write` solo nel job che salva l'artifact di stato) e il checkout **non conserva le credenziali** nel workspace (`persist-credentials: false`)
