import json
import os
import unittest
from urllib.parse import urlparse


class ConfigExampleTests(unittest.TestCase):
    def test_example_config_exists(self):
        path = os.path.join(os.path.dirname(__file__), os.pardir, "config.json.example")
        self.assertTrue(os.path.exists(path), "Il file config.json.example deve esistere")

    def test_example_config_product_urls_are_valid(self):
        path = os.path.join(os.path.dirname(__file__), os.pardir, "config.json.example")
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        self.assertIn("products", config)
        self.assertIsInstance(config["products"], list)
        self.assertGreater(len(config["products"]), 0)

        for product in config["products"]:
            self.assertIn("name", product)
            self.assertIn("url", product)
            self.assertIn("selector_price", product)
            self.assertIn("selector_original_price", product)

            parsed = urlparse(product["url"])
            self.assertIn(parsed.scheme, {"http", "https"}, f"URL non valida: {product['url']}")
            self.assertTrue(parsed.netloc, f"URL non valida: {product['url']}")

    def test_example_config_contains_amazon_or_ebay_links(self):
        path = os.path.join(os.path.dirname(__file__), os.pardir, "config.json.example")
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)

        domains = {urlparse(product["url"]).netloc for product in config["products"]}
        self.assertTrue(any("amazon." in domain for domain in domains) or any("ebay." in domain for domain in domains),
                        "I prodotti di esempio devono includere almeno un link Amazon o eBay")


if __name__ == "__main__":
    unittest.main()
