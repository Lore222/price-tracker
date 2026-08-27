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
                    "TELEGRAM_BOT_TOKEN": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
                    "TELEGRAM_CHAT_ID": "169943050",
                },
                clear=False,
            ):
                config = load_config(config_path)

            self.assertEqual(
                config["telegram"]["bot_token"], "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
            )
            self.assertEqual(config["telegram"]["chat_id"], "169943050")
            self.assertEqual(config["products"], [])
            self.assertEqual(config["check_interval_minutes"], 60)

    def test_load_config_validates_telegram_when_products_exist(self):
        """Test che la validazione Telegram fallisca se mancano campi con prodotti configurati."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {
                "telegram": {
                    "bot_token": "123456:ABC",
                    # manca chat_id
                },
                "products": [
                    {"name": "Test", "url": "https://example.com"}
                ],
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with self.assertRaises(ValueError) as ctx:
                load_config(config_path)

            self.assertIn("Configurazione Telegram incompleta", str(ctx.exception))

    def test_load_config_valid_telegram_with_products(self):
        """Test che una config Telegram completa con prodotti passi la validazione."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {
                "telegram": {
                    "bot_token": "123456:ABC",
                    "chat_id": "169943050",
                },
                "products": [
                    {"name": "Test", "url": "https://example.com"}
                ],
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            config = load_config(config_path)
            self.assertEqual(config["telegram"]["bot_token"], "123456:ABC")
            self.assertEqual(config["telegram"]["chat_id"], "169943050")
            self.assertEqual(len(config["products"]), 1)

    def test_load_config_exposes_nested_scraperapi_key(self):
        """La chiave nella sezione scraperapi viene resa disponibile al runner."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {
                "scraperapi": {"api_key": "config-key"},
                "telegram": {"bot_token": "123456:ABC", "chat_id": "169943050"},
                "products": [{"name": "Test", "url": "https://example.com"}],
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with patch.dict(os.environ, {}, clear=True):
                config = load_config(config_path)

            self.assertEqual(config["scraperapi_key"], "config-key")

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

    def test_load_config_validates_telegram_env_when_products_exist(self):
        """Test che la validazione Telegram fallisca se le env var sono incomplete con prodotti."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = os.path.join(tmpdir, "config.json")
            config_data = {
                "products": [
                    {"name": "Test", "url": "https://example.com"}
                ],
            }
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f)

            with patch.dict(
                os.environ,
                {"TELEGRAM_BOT_TOKEN": "123456:ABC"},  # manca chat_id
                clear=False,
            ):
                with self.assertRaises(ValueError) as ctx:
                    load_config(config_path)

            self.assertIn("chat id", str(ctx.exception))

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