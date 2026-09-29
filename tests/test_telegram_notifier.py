import unittest
from unittest import mock

import requests

from telegram_notifier import (
    _build_deals_message,
    _build_summary_message,
    _format_percent,
    _format_price,
    send_telegram_alert,
)


CONFIG = {"telegram": {"bot_token": "x", "chat_id": "1"}, "discount_threshold": 70}


class TelegramNotifierTests(unittest.TestCase):
    def test_format_price_missing_is_nd(self):
        self.assertEqual(_format_price(None), "N/D")

    def test_format_price_italian_style(self):
        self.assertEqual(_format_price(649), "649,00")
        self.assertEqual(_format_price(1234.56), "1.234,56")
        self.assertEqual(_format_price(649.0), "649,00")

    def test_format_percent_italian_style(self):
        self.assertEqual(_format_percent(13.35), "13,35")
        self.assertEqual(_format_percent(70.0), "70")
        self.assertEqual(_format_percent(None), "N/D")

    def test_summary_does_not_show_none_when_original_missing(self):
        """Regressione: prezzo originale assente non deve diventare '€None'."""
        products = [
            {
                "name": "Robottino",
                "url": "https://amazon.it/dp/X",
                "current_price": 649.0,
                "original_price": None,
                "discount_percent": None,
            }
        ]
        msg = _build_summary_message(CONFIG, products)
        self.assertIn("€649,00", msg)
        self.assertNotIn("€None", msg)
        self.assertIn("non disponibile", msg)

    def test_summary_formats_prices(self):
        products = [
            {
                "name": "Robottino",
                "url": "https://amazon.it/dp/X",
                "current_price": 649.0,
                "original_price": 749.0,
                "discount_percent": 13.35,
            }
        ]
        msg = _build_summary_message(CONFIG, products)
        self.assertIn("€649,00", msg)
        self.assertIn("€749,00", msg)
        self.assertIn("13,35%</b>", msg)

    def test_summary_shows_error_for_failed_product(self):
        products = [{"name": "Err", "url": "https://x.it", "error": "boom"}]
        msg = _build_summary_message(CONFIG, products)
        self.assertIn("Errore: boom", msg)

    def test_deals_message_formats_prices(self):
        deals = [
            {
                "name": "Prodotto",
                "url": "https://amazon.it/dp/Y",
                "current_price": 649.0,
                "original_price": 749.0,
                "discount_percent": 13.35,
            }
        ]
        msg = _build_deals_message(CONFIG, deals)
        self.assertIn("€649,00", msg)
        self.assertIn("€749,00", msg)
        self.assertIn("13,35%", msg)
        self.assertNotIn("€None", msg)

    def test_deals_message_does_not_se_nd_when_original_missing(self):
        # Caso anomalo ma difensivo: nessun '€N/D' barrato nei messaggi.
        deals = [
            {
                "name": "Prodotto",
                "url": "https://amazon.it/dp/Y",
                "current_price": 649.0,
                "original_price": None,
                "discount_percent": 13.35,
            }
        ]
        msg = _build_deals_message(CONFIG, deals)
        self.assertIn("€649,00", msg)
        self.assertNotIn("€None", msg)
        self.assertNotIn("€N/D", msg)


class TelegramSecretRedactionTests(unittest.TestCase):
    def _deals(self):
        return [
            {
                "name": "Prodotto",
                "url": "https://amazon.it/dp/Y",
                "current_price": 100.0,
                "original_price": 500.0,
                "discount_percent": 80.0,
            }
        ]

    def _config(self, token):
        return {"telegram": {"bot_token": token, "chat_id": "1"}, "discount_threshold": 70}

    def test_bot_token_is_not_logged_on_network_error(self):
        """Sicurezza: il token del bot è nell'URL di Telegram e le eccezioni di
        requests lo includono: non deve finire nei log."""
        token = "123456789:AAFakeTokenForRedactionTest"

        def fail(*args, **kwargs):
            raise requests.ConnectionError(
                f"Max retries exceeded with url: /bot{token}/sendMessage"
            )

        with mock.patch("telegram_notifier.requests.post", side_effect=fail), \
                self.assertLogs("telegram_notifier", level="ERROR") as captured:
            ok = send_telegram_alert(self._config(token), self._deals())

        self.assertFalse(ok)
        self.assertNotIn(token, "\n".join(captured.output))

    def test_bot_token_is_not_logged_on_http_error(self):
        """Sicurezza: anche una risposta HTTP di errore (401/400) contiene il
        token nell'URL e non deve comparire nei log."""
        token = "123456789:AAFakeTokenForRedactionTest"
        url = f"https://api.telegram.org/bot{token}/sendMessage"

        class FakeResponse:
            def raise_for_status(self):
                raise requests.HTTPError(
                    f"401 Client Error: Unauthorized for url: {url}"
                )

            def json(self):
                return {"ok": False, "description": "Unauthorized"}

        with mock.patch("telegram_notifier.requests.post", return_value=FakeResponse()), \
                self.assertLogs("telegram_notifier", level="ERROR") as captured:
            ok = send_telegram_alert(self._config(token), self._deals())

        self.assertFalse(ok)
        self.assertNotIn(token, "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()