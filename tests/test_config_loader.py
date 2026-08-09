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


if __name__ == "__main__":
    unittest.main()
