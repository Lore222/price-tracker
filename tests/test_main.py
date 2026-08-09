import argparse
import unittest

from main import should_run_continuously


class MainModeTests(unittest.TestCase):
    def test_defaults_to_single_run(self):
        self.assertFalse(should_run_continuously(None, {}))

    def test_loop_flag_enables_continuous_mode(self):
        args = argparse.Namespace(loop=True)
        self.assertTrue(should_run_continuously(args, {}))

    def test_env_flag_enables_continuous_mode(self):
        self.assertTrue(should_run_continuously(None, {"CONTINUOUS_MODE": "true"}))


if __name__ == "__main__":
    unittest.main()
