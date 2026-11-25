"""End-to-end checks of the 5-page sidebar navigation, unified dashboard, forms, settings, and export tools."""

import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.knowledge_engine import FOOD


APP = Path(__file__).resolve().parents[1] / "app.py"


class AppTests(unittest.TestCase):
    def test_sidebar_has_five_menu_pages_and_no_legacy_option(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        nav_radio = next(r for r in app.sidebar.radio if r.label == "Menu")
        self.assertEqual(
            list(nav_radio.options),
            [
                "📊 Dashboard",
                "➕ New Product",
                "🧪 New Ingredient",
                "🛠️ Tools & Export",
                "⚙️ Settings",
            ],
        )
        for r in app.sidebar.radio:
            self.assertNotIn("Legacy Sample Page", r.options)

    def test_dashboard_scorecard_explorer_and_simulation(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(app.exception)
        self.assertGreaterEqual(len(app.tabs), 4)
        self.assertEqual([item.value for item in app.error], ["Fail"] * 4)
        self.assertTrue(any("Porcine Gelatin" in item.value for item in app.markdown))
        self.assertTrue(any("Beetroot Red" in item.value for item in app.markdown))

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

    def test_new_product_and_new_ingredient_pages_workflow(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        nav_radio = next(r for r in app.sidebar.radio if r.label == "Menu")

        # 1. Go to New Product page and create a product
        nav_radio.set_value("➕ New Product").run()
        self.assertFalse(app.exception)
        prod_name = next(ti for ti in app.text_input if ti.label == "Product name")
        prod_name.input("Test Custom Product")
        create_prod_btn = next(btn for btn in app.button if "Create product" in btn.label)
        create_prod_btn.click().run()
        self.assertFalse(app.exception)

        # 2. Go to New Ingredient page and create a labelled ingredient attached to the product
        nav_radio = next(r for r in app.sidebar.radio if r.label == "Menu")
        nav_radio.set_value("🧪 New Ingredient").run()
        self.assertFalse(app.exception)
        ing_name = next(ti for ti in app.text_input if ti.label == "Ingredient name (rdfs:label)")
        ing_name.input("Extract")
        e_num_input = next(ti for ti in app.text_input if "E-Number" in ti.label)
        e_num_input.input("E999")
        eth_check = next(cb for cb in app.checkbox if "ethanol" in cb.label.lower())
        eth_check.check()
        eth_num = next(ni for ni in app.number_input if "ethanol" in ni.label.lower())
        eth_num.set_value(1.2)
        add_ing_btn = next(btn for btn in app.button if "Save ingredient" in btn.label)
        add_ing_btn.click().run()
        self.assertFalse(app.exception)

        # 3. Return to Dashboard and verify the new product & ingredient are evaluated
        nav_radio = next(r for r in app.sidebar.radio if r.label == "Menu")
        nav_radio.set_value("📊 Dashboard").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Ethanol exceeds" in item.label for item in app.expander))
        node_select = next(sb for sb in app.selectbox if sb.label == "Node details")
        self.assertIn("Extract", [ str(opt) for opt in node_select.options ] + [
            item.value for item in app.markdown
        ])

    def test_settings_and_tools_pages(self):
        app = AppTest.from_file(str(APP), default_timeout=30).run()
        nav_radio = next(r for r in app.sidebar.radio if r.label == "Menu")

        nav_radio.set_value("⚙️ Settings").run()
        self.assertFalse(app.exception)
        theme_radio = next(r for r in app.radio if "Theme" in r.label)
        font_select = next(sb for sb in app.selectbox if "Font size" in sb.label)
        theme_radio.set_value("🌞 Light (Day)").run()
        self.assertFalse(app.exception)
        font_select.set_value("Large (18px)").run()
        self.assertFalse(app.exception)

        nav_radio = next(r for r in app.sidebar.radio if r.label == "Menu")
        nav_radio.set_value("🛠️ Tools & Export").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Export" in item.value for item in list(app.title) + list(app.subheader)))

    def test_recovers_from_stale_session_recipe_without_add_product(self):
        class LegacyRecipeStub:
            pass

        app = AppTest.from_file(str(APP), default_timeout=30)
        app.session_state["recipe"] = LegacyRecipeStub()
        app.run()
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
