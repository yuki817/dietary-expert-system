"""End-to-end checks of the sample workflows without a browser."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def test_sample_scorecard_explorer_and_simulation(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertEqual([item.value for item in app.error], ["Fail"] * 4)
        self.assertTrue(any("Porcine Gelatin" in item.value for item in app.markdown))

        app.sidebar.radio[0].set_value("Supply chain explorer").run()
        self.assertFalse(app.exception)
        self.assertIn("Porcine Gelatin", app.selectbox[1].options)

        app.sidebar.radio[0].set_value("Reformulation advisor").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Beetroot Red" in item.value for item in app.markdown))
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any(item.value == "Simulated product results" for item in app.subheader))
        self.assertTrue(any("Not assessed" in item.value for item in app.markdown))

    def test_custom_recipe_is_evaluated_and_explorable(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        app.sidebar.text_input[0].input("Test recipe")
        app.sidebar.button[0].click().run()
        self.assertFalse(app.exception)
        app.sidebar.text_input[0].input("Extract")
        app.sidebar.checkbox[0].check()
        app.sidebar.number_input[0].set_value(1.2)
        app.sidebar.button[1].click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Ethanol exceeds" in item.label for item in app.expander))
        app.sidebar.radio[0].set_value("Supply chain explorer").run()
        self.assertFalse(app.exception)
        self.assertIn("Extract", app.selectbox[1].options)
