import unittest

from scraper import extract_price_data_from_html


class ScraperParsingTests(unittest.TestCase):
    def test_extract_price_data_uses_fallback_selectors(self):
        html = """
        <html><body>
            <div id="price-block">
                <span class="a-price-whole">649</span>
            </div>
            <div id="original-price-block">
                <span class="a-text-price"><span class="a-offscreen">749,00€</span></span>
            </div>
        </body></html>
        """

        data = extract_price_data_from_html(
            html,
            ["#missing-selector", "span.a-price-whole"],
            ["#missing-original", "span.a-text-price span.a-offscreen"],
        )

        self.assertEqual(data["current_price"], 649.0)
        self.assertEqual(data["original_price"], 749.0)
        self.assertEqual(data["discount_percent"], 13.35)

    def test_extract_price_data_falls_back_to_regex_values(self):
        html = """
        <html><body>
            <div>Prezzo attuale: 649,00€</div>
            <div>Prezzo originale: 749,00€</div>
        </body></html>
        """

        data = extract_price_data_from_html(
            html,
            ["#missing-price"],
            ["#missing-original"],
        )

        self.assertEqual(data["current_price"], 649.0)
        self.assertEqual(data["original_price"], 749.0)


if __name__ == "__main__":
    unittest.main()
