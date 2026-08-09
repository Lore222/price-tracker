import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, List


def _create_ssl_context():
    """Crea un contesto SSL permissive per compatibilità con vari server."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context


def _connect_smtp(email_config: Dict):
    """Tenta di connettersi al server SMTP con diverse configurazioni."""
    server = None
    errors = []

    # Prova SSL diretto (porta 465)
    try:
        context = _create_ssl_context()
        server = smtplib.SMTP_SSL(
            email_config["smtp_server"],
            email_config.get("smtp_port_ssl", 465),
            timeout=20,
            context=context,
        )
        return server
    except Exception as e:
        errors.append(f"SSL 465: {e}")

    # Prova STARTTLS (porta 587)
    try:
        server = smtplib.SMTP(
            email_config["smtp_server"],
            email_config.get("smtp_port", 587),
            timeout=20,
        )
        server.starttls(context=_create_ssl_context())
        return server
    except Exception as e:
        errors.append(f"STARTTLS 587: {e}")

    # Prova senza TLS (porta 25)
    try:
        server = smtplib.SMTP(
            email_config["smtp_server"],
            email_config.get("smtp_port_plain", 25),
            timeout=20,
        )
        return server
    except Exception as e:
        errors.append(f"Plain 25: {e}")

    raise ConnectionError(f"Impossibile connettersi al server SMTP: {'; '.join(errors)}")


def send_alert_email(config: Dict, deals: List[Dict]) -> bool:
    """Invia un'email di alert con le offerte trovate."""
    if not deals:
        return False

    email_config = config["email"]
    subject = f"🔥 {len(deals)} OFFERTE IMPERDIBILI - Sconto oltre {config['discount_threshold']}%!"

    body = f"""
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
    <div style="max-width: 600px; margin: auto; background: white; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
        <h1 style="color: #e74c3c; text-align: center;">🔥 Offerte Imperdibili!</h1>
        <p style="text-align: center; color: #555;">Trovate <strong>{len(deals)}</strong> offerte con sconto superiore al {config['discount_threshold']}%</p>
        <hr style="border: 1px solid #eee;">
"""

    for deal in deals:
        discount = deal.get("discount_percent", 0)
        current = deal.get("current_price", "N/D")
        original = deal.get("original_price", "N/D")
        body += f"""
        <div style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 15px 0; background: #fafafa;">
            <h3 style="margin: 0 0 10px 0; color: #333;">{deal['name']}</h3>
            <p style="margin: 5px 0;">
                <span style="color: #e74c3c; font-size: 20px; font-weight: bold;">€{current}</span>
                <span style="color: #999; text-decoration: line-through; margin-left: 10px;">€{original}</span>
            </p>
            <p style="margin: 5px 0; color: #27ae60; font-weight: bold;">Sconto: {discount}%</p>
            <a href="{deal['url']}" style="display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px;">Vai all'offerta →</a>
        </div>
"""

    body += """
        <hr style="border: 1px solid #eee;">
        <p style="text-align: center; color: #999; font-size: 12px;">Monitoraggio prezzi automatico - Controllo ogni 30 minuti</p>
    </div>
</body>
</html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = email_config["sender_email"]
    msg["To"] = email_config["recipient_email"]
    msg.attach(MIMEText(body, "html"))

    try:
        server = _connect_smtp(email_config)
        server.login(email_config["sender_email"], email_config["sender_password"])
        server.send_message(msg)
        server.quit()
        print(f"  ✅ Email inviata con {len(deals)} offerte")
        return True
    except Exception as e:
        print(f"  ❌ Errore invio email: {e}")
        return False