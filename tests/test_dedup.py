import os
import tempfile
import unittest

from main import _filter_unnotified
from state_store import StateStore


class StateStoreTests(unittest.TestCase):
    def test_roundtrip_persists_after_save(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "state.json")
            store = StateStore(path)
            store.set("offer:https://x.it/1", 42.0)
            store.save()

            store2 = StateStore(path)
            self.assertEqual(store2.get("offer:https://x.it/1"), 42.0)

    def test_missing_file_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(os.path.join(tmpdir, "nope.json"))
            self.assertEqual(store.get("offer:https://x.it/1"), None)

    def test_corrupt_file_resets(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "state.json")
            with open(path, "w", encoding="utf-8") as f:
                f.write("{not valid json")
            store = StateStore(path)
            self.assertEqual(store.get("offer:https://x.it/1"), None)


class NotifiedFilterTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.state = StateStore(os.path.join(self._tmpdir.name, "state.json"))

    def deals(self, *discounts):
        deals = []
        for i, d in enumerate(discounts):
            deals.append(
                {"name": f"P{i}", "url": f"https://x.it/{i}", "discount_percent": d}
            )
        return deals

    def test_notifies_first_time_and_skips_unchanged(self):
        deals = self.deals(50.0, 60.0)
        first = _filter_unnotified(self.state, deals)
        self.assertEqual([d["name"] for d in first], ["P0", "P1"])

        # Seconda run: stesse offerte, nessun nuovo alert.
        second = _filter_unnotified(self.state, deals)
        self.assertEqual(second, [])

    def test_notifies_when_discount_improves(self):
        deals = self.deals(50.0)
        self.assertEqual(_filter_unnotified(self.state, deals), deals)

        improved = self.deals(55.0)  # +5 punti, sopra la soglia min_improvement di 2
        notified = _filter_unnotified(self.state, improved)
        self.assertEqual([d["name"] for d in notified], ["P0"])

    def test_skips_small_improvement_below_threshold(self):
        deals = self.deals(50.0)
        self.assertEqual(len(_filter_unnotified(self.state, deals)), 1)

        slightly_improved = self.deals(51.0)  # +1 punto sotto soglia
        notified = _filter_unnotified(self.state, slightly_improved)
        self.assertEqual(notified, [])


if __name__ == "__main__":
    unittest.main()