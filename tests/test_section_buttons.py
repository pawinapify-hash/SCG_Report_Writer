from pathlib import Path
import unittest
from unittest.mock import patch

import pandas as pd
from streamlit.testing.v1 import AppTest

from report_writer.ces_data import CES_METRICS


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


class SectionButtonTests(unittest.TestCase):
    def test_individual_section_buttons_exist_and_overviews_start_disabled(self):
        app = AppTest.from_file(APP_PATH, default_timeout=20).run()

        self.assertFalse(app.exception)
        buttons = {button.label: button for button in app.button}
        self.assertIn("Analyze Key Thematic", buttons)
        self.assertIn("Analyze Top PRI Content", buttons)
        self.assertIn("Analyze Overview CES", buttons)
        self.assertIn("Analyze PRE Overview", buttons)
        self.assertIn("Generate All Analysis", buttons)
        self.assertTrue(buttons["Analyze Overview CES"].disabled)
        self.assertTrue(buttons["Analyze PRE Overview"].disabled)

    def test_overview_ces_enables_after_complete_key_thematic_results(self):
        score_rows = []
        analyses = []
        for brand, score in (("SCG", 50), ("PTT", 40), ("CP", 30)):
            row = {"Pillar": "ESG Branding", "Brand": brand}
            for metric in CES_METRICS:
                row[metric] = score
                row[metric + " Growth"] = 1
            score_rows.append(row)
            analyses.append({
                "section": "CES Key Thematic",
                "pillar": "ESG Branding",
                "brand": brand,
                "title": f"CES ESG {brand} Key Thematic",
                "output": f"{brand} output",
                "error": None,
                "messages": [
                    {"role": "system", "content": "test"},
                    {"role": "user", "content": "test"},
                ],
            })

        app = AppTest.from_file(APP_PATH, default_timeout=20)
        app.session_state["ces_df"] = pd.DataFrame(score_rows)
        app.session_state["analyses"] = analyses
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            app.run()

        self.assertFalse(app.exception)
        buttons = {button.label: button for button in app.button}
        self.assertFalse(buttons["Analyze Overview CES"].disabled)


if __name__ == "__main__":
    unittest.main()
