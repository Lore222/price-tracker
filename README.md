# 🛒 Price Tracker - Monitoraggio Offerte E-commerce

Programma Python che monitora i prezzi su vari siti e-commerce ogni 30 minuti e invia un'email di alert quando trova prodotti con sconto superiore al 90%.

## ✨ Funzionalità

- 🔍 Controllo automatico dei prezzi ogni 30 minuti (configurabile)
- 📧 Invio email HTML con le offerte trovate
- 🎯 Soglia sconto configurabile (default: 90%)
- 🌐 Supporto multi-sito (Amazon, eBay, e altri)
- 📊 Calcolo automatico della percentuale di sconto
- 🛡️ Gestione errori di rete e parsing

## 📋 Requisiti

- Python 3.8+
- Un account email con SMTP (es. Gmail con App Password)

## 🚀 Installazione

```bash
cd price-tracker
pip install -r requirements.txt
```

## ⚙️ Configurazione

### 1. Configurare l'email (config.json)

**Per Virgilio/Tiscali (Italiaonline):**
```json
"email": {
    "smtp_server": "smtp.virgilio.it",
    "smtp_port": 587,
    "smtp_port_ssl": 465,
    "smtp_port_plain": 25,
    "sender_email": "IL_TUO_EMAIL@virgilio.it",
    "sender_password": "LA_TUA_PASSWORD",
    "recipient_email": "DESTINATARIO@example.com"
}
```

**Per Gmail:**
1. Attiva la verifica in due passaggi su [myaccount.google.com](https://myaccount.google.com)
2. Vai su Sicurezza → Password per le app
3. Genera una password per l'app "Mail"
4. Inserisci i dati nel file `config.json`:

```json
"email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "IL_TUO_EMAIL@gmail.com",
    "sender_password": "LA_TUA_PASSWORD_APP",
    "recipient_email": "DESTINATARIO@example.com"
}
```


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
| `check_interval_minutes` | Intervallo controlli in minuti | 30 |
| `discount_threshold` | Soglia sconto per alert (%) | 90 |

## ▶️ Utilizzo

```bash
python main.py
```

Il programma:
1. Esegue subito un primo controllo
2. Poi controlla automaticamente ogni 30 minuti
3. Invia un'email quando trova offerte con sconto ≥ 90%

Per fermare: `Ctrl+C`

## 📁 Struttura del progetto

```
price-tracker/
├── main.py              # Punto di ingresso con scheduler
├── config.json          # Configurazione email e prodotti
├── config_loader.py     # Caricamento e validazione configurazione
├── scraper.py           # Estrazione prezzi dai siti
├── email_notifier.py    # Invio email di alert
└── requirements.txt     # Dipendenze Python
```

## ⚠️ Note importanti

- **Rispetta i siti web**: il programma attende 2 secondi tra una richiesta e l'altra
- **Selettori CSS**: possono cambiare se il sito aggiorna il layout, aggiorna i selettori in `config.json`
- **Anti-bot**: alcuni siti potrebbero bloccare lo scraping, in tal caso usa un User-Agent diverso o un proxy
- **Gmail**: usa una App Password, non la password normale dell'account

## 🔒 Privacy

- Le credenziali email sono salvate localmente in `config.json`
- Nessun dato viene inviato a terze parti
- Le richieste vanno direttamente ai siti e-commerce configurati