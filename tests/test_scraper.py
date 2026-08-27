import unittest
from unittest import mock

from scraper import (
    _calculate_discount,
    _extract_prices_from_html_fallback,
    _get_via_scraperapi,
    _is_anti_bot_page,
    _parse_price,
    check_all_products,
    extract_price_data_from_html,
    fetch_product_price,
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
        """Il fallback regex recupera solo il prezzo attuale; il prezzo originale
        non deve essere dedotto dall'ordine di apparizione dei prezzi."""
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
        self.assertIsNone(data["original_price"])
        self.assertIsNone(data["discount_percent"])

    def test_extract_price_data_supports_euro_before_number(self):
        """Test che il fallback regex gestisca € prima del numero (solo prezzo attuale)."""
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
        self.assertIsNone(data["original_price"])

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
        self.assertIsNone(data["original_price"])
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
        self.assertIsNone(data["original_price"])
        self.assertIsNone(data["discount_percent"])

    def test_extract_price_data_does_not_guess_original_from_unrelated_prices(self):
        """Regressione: il prezzo originale non deve essere dedotto dal secondo
        importo € nella pagina, altrimenti arrivano sconti/notifiche sbagliati."""
        html = """
        <html><body>
            <span class="a-price-whole">399</span>
            <span class="price-ship">Spedizione: 9,99€</span>
            <div class="compare">Confronta: 1399,00€</div>
        </body></html>
        """

        # Il prezzo attuale viene trovato, ma il selettore del prezzo originale
        # fallisce: il bot NON deve inventare 1399,00€ come prezzo di listino.
        data = extract_price_data_from_html(
            html,
            ["#missing", "span.a-price-whole"],
            ["span.a-text-price span.a-offscreen"],
        )

        self.assertEqual(data["current_price"], 399.0)
        self.assertIsNone(data["original_price"])
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

    def test_extract_price_data_single_fallback_price_sets_only_current(self):
        """Test che un solo prezzo fallback venga usato solo come prezzo attuale."""
        html = "<html><body><div>Prezzo: 649,00€</div></body></html>"

        data = extract_price_data_from_html(
            html,
            ["#missing-price"],
            ["#missing-original"],
        )

        self.assertEqual(data["current_price"], 649.0)
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

    def test_extract_prices_from_html_fallback_eur_format(self):
        """Il fallback regex deve leggere anche il formato 'EUR' usato su eBay
        Italia (es. 'EUR 1.099,00' oppure '1.099,00 EUR')."""
        html = """
        <div>EUR 1.099,00</div>
        <div>1.299,00 EUR</div>
        """
        prices = _extract_prices_from_html_fallback(html)
        self.assertIn(1099.0, prices)
        self.assertIn(1299.0, prices)

    def test_extract_price_data_ebay_selectors(self):
        """Verifica che i selettori standard di eBay (BOLD per il prezzo attuale,
        STRIKETHROUGH per quello originale) estraggano i prezzi correttamente."""
        html = """
        <html><body>
            <div class="x-price-primary">
                <span class="ux-textspans ux-textspans--BOLD">EUR 1.099,00</span>
            </div>
            <div class="ux-price-strike">
                <span class="ux-textspans ux-textspans--STRIKETHROUGH">EUR 1.599,00</span>
            </div>
        </body></html>
        """
        data = extract_price_data_from_html(
            html,
            ["span.ux-textspans--BOLD"],
            ["span.ux-textspans--STRIKETHROUGH"],
        )
        self.assertEqual(data["current_price"], 1099.0)
        self.assertEqual(data["original_price"], 1599.0)
        self.assertEqual(data["discount_percent"], 31.27)


class ScraperApiIntegrationTests(unittest.TestCase):
    """Test dell'integrazione con il proxy ScraperAPI."""

    def test_get_via_scraperapi_sends_correct_payload(self):
        """Verifica che ScraperAPI riceva api_key e url come parametri corretti."""
        with mock.patch("scraper.requests.get") as mocked_get:
            mocked_get.return_value = mock.Mock(text="<html></html>", raise_for_status=lambda: None)
            _get_via_scraperapi("https://www.amazon.it/dp/EXAMPLE", "api-key-test")
            mocked_get.assert_called_once_with(
                "https://api.scraperapi.com/",
                params={"api_key": "api-key-test", "url": "https://www.amazon.it/dp/EXAMPLE"},
                timeout=30,
            )

    def test_fetch_product_price_uses_scraperapi_when_key_given(self):
        """Con una chiave, fetch_product_price passa dal proxy ScraperAPI."""
        html = '<span class="a-price-whole">649</span>'
        with mock.patch("scraper.requests.get") as mocked_get:
            mocked_get.return_value = mock.Mock(text=html, raise_for_status=lambda: None)
            data = fetch_product_price(
                "https://www.amazon.it/dp/EXAMPLE",
                "span.a-price-whole",
                None,
                scraperapi_key="KEY",
                timeout=45,
            )
            self.assertEqual(data["current_price"], 649.0)
            self.assertEqual(mocked_get.call_args[0][0], "https://api.scraperapi.com/")
            self.assertEqual(mocked_get.call_args[1]["params"]["api_key"], "KEY")
            self.assertEqual(mocked_get.call_args[1]["timeout"], 45)

    def test_fetch_product_price_uses_direct_request_without_key(self):
        """Senza chiave, fetch_product_price fa una richiesta diretta."""
        html = '<span class="a-price-whole">399</span>'
        with mock.patch("scraper.requests.get") as mocked_get:
            mocked_get.return_value = mock.Mock(text=html, raise_for_status=lambda: None)
            data = fetch_product_price("https://www.amazon.it/dp/EXAMPLE", "span.a-price-whole", None)
            self.assertEqual(data["current_price"], 399.0)
            self.assertEqual(mocked_get.call_args[0][0], "https://www.amazon.it/dp/EXAMPLE")
            self.assertNotIn("api_key", mocked_get.call_args[1].get("params", {}))

    def test_is_anti_bot_page_detects_verification_page(self):
        """Rileva una pagina di verifica/anti-bot (es. Amazon)."""
        html = (
            "<html><body>Per continuare a fare acquisti, inserisci i caratteri "
            "qui sotto. <span>€10.0</span> <span>€5.99</span></body></html>"
        )
        self.assertTrue(_is_anti_bot_page(html))

    def test_is_anti_bot_page_does_not_flag_normal_page(self):
        """Una pagina prodotto normale non deve essere rilevata come anti-bot."""
        html = '<html><body><span class="a-price-whole">649,00</span></body></html>'
        self.assertFalse(_is_anti_bot_page(html))

    def test_is_anti_bot_page_does_not_flag_robot_product_title(self):
        """La parola 'robot' nel titolo di un prodotto non indica un blocco."""
        html = '<html><title>Robot aspirapolvere</title><span class="a-price-whole">399</span></html>'
        self.assertFalse(_is_anti_bot_page(html))

    def test_fetch_product_price_returns_error_on_anti_bot_page(self):
        """Regressione: su una pagina anti-bot con importi € casuali, il bot deve
        restituire un errore chiaro e NON un prezzo falso (es. €10.0)."""
        html = (
            "<html><body>Per continuare a fare acquisti, inserisci i caratteri "
            "qui sotto. <span>€10.0</span> <span>€5.99</span></body></html>"
        )
        with mock.patch("scraper.requests.get") as mocked_get:
            mocked_get.return_value = mock.Mock(text=html, raise_for_status=lambda: None)
            data = fetch_product_price(
                "https://www.amazon.it/dp/EXAMPLE",
                "span.a-price-whole",
                "span.a-text-price span.a-offscreen",
            )
            self.assertIn("error", data)
            self.assertIn("anti-bot", data["error"])
            self.assertNotIn("current_price", data)


class PriceCacheTests(unittest.TestCase):
    def test_reuses_price_within_cache_window(self):
        product = {
            "name": "Test product",
            "url": "https://example.com/unique-cache-test",
            "selector_price": "span.price",
        }
        fetched_data = {"current_price": 10.0, "original_price": None, "discount_percent": None}

        with mock.patch("scraper.fetch_product_price", return_value=fetched_data) as mocked_fetch:
            with mock.patch("scraper.time.sleep"):
                first_results = check_all_products([product], cache_ttl_minutes=60)
                second_results = check_all_products([product], cache_ttl_minutes=60)

        mocked_fetch.assert_called_once()
        self.assertEqual(first_results, second_results)


if __name__ == "__main__":
    unittest.main()