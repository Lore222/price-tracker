# 🛒 Price Tracker - Monitoraggio Offerte E-commerce

Programma Python che monitora i prezzi su vari siti e-commerce ogni 30 minuti e invia un messaggio Telegram di alert quando trova prodotti con sconto superiore al 90%.

## ✨ Funzionalità

- 🔍 Controllo automatico dei prezzi ogni ora (configurabile)
- 📨 Invio messaggi Telegram con le offerte trovate
- 🎯 Soglia sconto configurabile (default: 90%)
- 🌐 Supporto multi-sito (Amazon, eBay, e altri)
- 📊 Calcolo automatico della percentuale di sconto
- 🛡️ Gestione errori di rete e parsing

## 📋 Requisiti

- Python 3.8+
- Un bot Telegram con il suo token e un chat ID (vedi sotto)

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

### 3. Impostazioni personalizzate

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `check_interval_minutes` | Intervallo controlli in minuti | 60 |
| `discount_threshold` | Soglia sconto per alert (%) | 70 |

## ▶️ Utilizzo

```bash
python main.py
```

Il programma:
1. Esegue subito un primo controllo
2. Poi controlla automaticamente ogni ora
3. Invia un messaggio Telegram quando trova offerte con sconto ≥ 70%

Per fermare: `Ctrl+C`

## 📁 Struttura del progetto

```
price-tracker/
├── main.py              # Punto di ingresso con scheduler
├── config.json          # Configurazione Telegram e prodotti
├── config_loader.py     # Caricamento e validazione configurazione
├── scraper.py           # Estrazione prezzi dai siti
├── telegram_notifier.py # Invio messaggi Telegram di alert
└── requirements.txt     # Dipendenze Python
```

## ⚠️ Note importanti

- **Rispetta i siti web**: il programma attende 2 secondi tra una richiesta e l'altra
- **Selettori CSS**: possono cambiare se il sito aggiorna il layout, aggiorna i selettori in `config.json`
- **Anti-bot**: alcuni siti potrebbero bloccare lo scraping, in tal caso usa un User-Agent diverso o un proxy
- **Telegram**: il bot token è un segreto, non condividerlo pubblicamente (il file `config.json` è già in `.gitignore`)

## 🔒 Privacy

- Il bot token Telegram è salvato localmente in `config.json` (in `.gitignore`)
- Nessun dato viene inviato a terze parti
- Le richieste vanno direttamente ai siti e-commerce configurati