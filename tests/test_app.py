"""End-to-end checks of the unified dashboard, sidebar authoring, and theme/font controls."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.knowledge_engine import FOOD


APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def test_sample_scorecard_explorer_and_simulation(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        # Main page renders all 4 unified tabs at once
        self.assertGreaterEqual(len(app.tabs), 3)
        self.assertEqual([item.value for item in app.error], ["Fail"] * 4)
        self.assertTrue(any("Porcine Gelatin" in item.value for item in app.markdown))
        self.assertTrue(any("Beetroot Red" in item.value for item in app.markdown))

        # Trigger single-ingredient simulation button in Reformulation tab
        sim_btn = next(btn for btn in app.button if "Simulate reformulation" in btn.label)
        sim_btn.click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any(item.value == "Simulated product results" for item in app.subheader))

    def test_plant_based_ramen_displays_green_pass_cards(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        product_select = next(sb for sb in app.selectbox if sb.label == "Product")
        product_select.set_value(FOOD.PlantBasedRamen).run()
        self.assertFalse(app.exception)
        self.assertEqual([item.value for item in app.success], ["Pass"] * 4)

    def test_custom_recipe_is_evaluated_and_explorable(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        recipe_input = next(ti for ti in app.sidebar.text_input if ti.label == "Recipe name")
        recipe_input.input("Test recipe")
        create_btn = next(btn for btn in app.sidebar.button if "Create" in btn.label)
        create_btn.click().run()
        self.assertFalse(app.exception)

        ing_input = next(ti for ti in app.sidebar.text_input if ti.label == "New ingredient name")
        ing_input.input("Extract")
        eth_check = next(cb for cb in app.sidebar.checkbox if "ethanol" in cb.label.lower())
        eth_check.check()
        eth_num = next(ni for ni in app.sidebar.number_input if "ethanol" in ni.label.lower())
        eth_num.set_value(1.2)
        add_btn = next(btn for btn in app.sidebar.button if "Add ingredient" in btn.label)
        add_btn.click().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Ethanol exceeds" in item.label for item in app.expander))
        node_select = next(sb for sb in app.selectbox if sb.label == "Node details")
        self.assertIn("Extract", node_select.options)

    def test_theme_mode_and_font_size_controls_in_sidebar(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        theme_radio = next(r for r in app.sidebar.radio if "Theme" in r.label)
        font_select = next(sb for sb in app.sidebar.selectbox if "Font size" in sb.label)
        theme_radio.set_value("🌞 Light (Day)").run()
        self.assertFalse(app.exception)
        font_select.set_value("Large (18px)").run()
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
