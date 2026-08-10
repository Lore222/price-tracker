import json
import os
import tempfile
import unittest
from unittest.mock import patch

from config_loader import load_config


class ConfigLoaderTests(unittest.TestCase):
    def test_load_config_uses_environment_when_file_is_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            with patch.dict(
                os.environ,
                {
                    "SMTP_SERVER": "smtp.example.com",
                    "SENDER_EMAIL": "sender@example.com",
                    "SENDER_PASSWORD": "secret",
                    "RECIPIENT_EMAIL": "recipient@example.com",
                },
                clear=False,
            ):
                config = load_config(config_path)

            self.assertEqual(config["email"]["smtp_server"], "smtp.example.com")
            self.assertEqual(config["products"], [])
            self.assertEqual(config["check_interval_minutes"], 60)

    def test_load_config_validates_email_when_products_exist(self):
        """Test che la validazione email fallisca se mancano campi con prodotti configurati."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {
                "email": {
                    "smtp_server": "smtp.example.com",
                    "sender_email": "sender@example.com",
                    # manca sender_password e recipient_email
                },
                "products": [
                    {"name": "Test", "url": "https://example.com"}
                ],
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path)

            self.assertIn("Configurazione email incompleta", str(ctx.exception))

    def test_load_config_valid_email_with_products(self):
        """Test che una config email completa con prodotti passi la validazione."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {
                "email": {
                    "smtp_server": "smtp.example.com",
                    "sender_email": "sender@example.com",
                    "sender_password": "secret",
                    "recipient_email": "recipient@example.com",
                },
                "products": [
                    {"name": "Test", "url": "https://example.com"}
                ],
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            config = load_config(config_path)
            self.assertEqual(config["email"]["smtp_server"], "smtp.example.com")
            self.assertEqual(len(config["products"]), 1)

    def test_load_config_invalid_env_int(self):
        """Test che una variabile d'ambiente non numerica sollevi ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            with patch.dict(
                os.environ,
                {"CHECK_INTERVAL_MINUTES": "abc"},
                clear=False,
            ):
                with self.assertRaises(ValueError) as ctx:
                    load_config(config_path)

            self.assertIn("CHECK_INTERVAL_MINUTES", str(ctx.exception))

    def test_load_config_invalid_env_float(self):
        """Test che una variabile d'ambiente non numerica per soglia sollevi ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            with patch.dict(
                os.environ,
                {"DISCOUNT_THRESHOLD": "abc"},
                clear=False,
            ):
                with self.assertRaises(ValueError) as ctx:
                    load_config(config_path)

            self.assertIn("DISCOUNT_THRESHOLD", str(ctx.exception))

    def test_load_config_invalid_smtp_port(self):
        """Test che SMTP_PORT non numerico sollevi ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")

            with patch.dict(
                os.environ,
                {
                    "SMTP_SERVER": "smtp.example.com",
                    "SMTP_PORT": "not-a-number",
                    "SENDER_EMAIL": "sender@example.com",
                    "SENDER_PASSWORD": "secret",
                    "RECIPIENT_EMAIL": "recipient@example.com",
                },
                clear=False,
            ):
                with self.assertRaises(ValueError) as ctx:
                    load_config(config_path)

            self.assertIn("SMTP_PORT", str(ctx.exception))

    def test_load_config_products_not_list(self):
        """Test che products non lista sollevi ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {"products": "not-a-list"}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path)

            self.assertIn("products", str(ctx.exception))

    def test_load_config_product_missing_fields(self):
        """Test che un prodotto senza name/url sollevi ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {"products": [{"name": "Solo nome"}]}
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path)

            self.assertIn("name", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()