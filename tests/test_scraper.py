import unittest

from scraper import (
    _calculate_discount,
    _extract_prices_from_html_fallback,
    _parse_price,
    extract_price_data_from_html,
)


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

    def test_extract_price_data_supports_euro_before_number(self):
        """Test che il fallback regex gestisca € prima del numero."""
        html = """
        <html><body>
            <div>Prezzo attuale: €649,00</div>
            <div>Prezzo originale: € 749,00</div>
        </body></html>
        """

        data = extract_price_data_from_html(
            html,
            ["#missing-price"],
            ["#missing-original"],
        )

        self.assertEqual(data["current_price"], 649.0)
        self.assertEqual(data["original_price"], 749.0)

    def test_extract_price_data_handles_price_increase(self):
        """Test che un aumento di prezzo non produca sconto negativo."""
        html = """
        <html><body>
            <div>Prezzo attuale: 799,00€</div>
            <div>Prezzo originale: 749,00€</div>
        </body></html>
        """

        data = extract_price_data_from_html(
            html,
            ["#missing-price"],
            ["#missing-original"],
        )

        self.assertEqual(data["current_price"], 799.0)
        self.assertEqual(data["original_price"], 749.0)
        self.assertIsNone(data["discount_percent"])

    def test_extract_price_data_handles_same_price(self):
        """Test che prezzo uguale non produca sconto."""
        html = """
        <html><body>
            <div>Prezzo attuale: 749,00€</div>
            <div>Prezzo originale: 749,00€</div>
        </body></html>
        """

        data = extract_price_data_from_html(
            html,
            ["#missing-price"],
            ["#missing-original"],
        )

        self.assertEqual(data["current_price"], 749.0)
        self.assertEqual(data["original_price"], 749.0)
        self.assertIsNone(data["discount_percent"])

    def test_extract_price_data_handles_no_prices(self):
        """Test che senza prezzi restituisca None."""
        html = "<html><body><div>Nessun prezzo qui</div></body></html>"

        data = extract_price_data_from_html(
            html,
            ["#missing-price"],
            ["#missing-original"],
        )

        self.assertIsNone(data["current_price"])
        self.assertIsNone(data["original_price"])
        self.assertIsNone(data["discount_percent"])

    def test_parse_price_italian_format(self):
        """Test parsing formato italiano (1.234,56)."""
        self.assertEqual(_parse_price("1.234,56"), 1234.56)
        self.assertEqual(_parse_price("649,00"), 649.0)
        self.assertEqual(_parse_price("649"), 649.0)

    def test_parse_price_international_format(self):
        """Test parsing formato internazionale (1,234.56)."""
        self.assertEqual(_parse_price("1,234.56"), 1234.56)
        self.assertEqual(_parse_price("649.00"), 649.0)

    def test_parse_price_invalid(self):
        """Test parsing valori non validi."""
        self.assertIsNone(_parse_price(""))
        self.assertIsNone(_parse_price("abc"))
        self.assertIsNone(_parse_price(None))

    def test_calculate_discount_normal(self):
        """Test calcolo sconto normale."""
        self.assertEqual(_calculate_discount(649.0, 749.0), 13.35)

    def test_calculate_discount_no_original(self):
        """Test sconto senza prezzo originale."""
        self.assertIsNone(_calculate_discount(649.0, None))
        self.assertIsNone(_calculate_discount(649.0, 0))

    def test_calculate_discount_price_increase(self):
        """Test sconto con aumento di prezzo."""
        self.assertIsNone(_calculate_discount(799.0, 749.0))

    def test_calculate_discount_same_price(self):
        """Test sconto con prezzo uguale."""
        self.assertIsNone(_calculate_discount(749.0, 749.0))

    def test_extract_prices_from_html_fallback_both_formats(self):
        """Test fallback regex con € prima e dopo."""
        html = """
        <div>€649,00</div>
        <div>749,00€</div>
        <div>€ 599,00</div>
        """
        prices = _extract_prices_from_html_fallback(html)
        self.assertIn(649.0, prices)
        self.assertIn(749.0, prices)
        self.assertIn(599.0, prices)


if __name__ == "__main__":
    unittest.main()