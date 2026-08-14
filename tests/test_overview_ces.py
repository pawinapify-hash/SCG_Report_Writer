import unittest

from report_writer.overview_ces import (
    build_overview_ces_messages,
    calculate_ces_rankings,
    overview_ces_validation_error,
)


def ces_row(score):
    return {
        "CES Score": score,
        "CES Score Growth": 1.0,
        "Competitive Score": 40.0,
        "Competitive Score Growth": 2.0,
        "Efficiency Score": 30.0,
        "Efficiency Score Growth": -1.0,
        "Sentiment (Influencer & Publisher)": 50.0,
        "Sentiment (Influencer & Publisher) Growth": 0.0,
        "Sentiment (Consumer)": 60.0,
        "Sentiment (Consumer) Growth": 3.0,
    }


class OverviewCesTests(unittest.TestCase):
    def test_rankings_and_star_support_tied_top_scores(self):
        rankings = calculate_ces_rankings({
            "SCG": ces_row(50),
            "PTT": ces_row(50),
            "CP": ces_row(40),
        })

        self.assertEqual(rankings["SCG"]["rank"], 1)
        self.assertEqual(rankings["PTT"]["rank"], 1)
        self.assertEqual(rankings["CP"]["rank"], 3)
        self.assertTrue(rankings["SCG"]["is_top"])
        self.assertTrue(rankings["PTT"]["is_top"])
        self.assertFalse(rankings["CP"]["is_top"])

    def test_message_uses_fixed_brand_order_and_exact_ranked_prefixes(self):
        rows = {
            "SCG": ces_row(43.9),
            "PTT": ces_row(53.3),
            "CP": ces_row(36.2),
        }
        key_thematics = {
            "SCG": "SCG thematic evidence",
            "PTT": "PTT thematic evidence",
            "CP": "CP thematic evidence",
        }

        messages = build_overview_ces_messages(
            "ESG Branding", rows, key_thematics, instruction="overview instruction"
        )
        content = messages[1]["content"]

        self.assertEqual(messages[0]["content"], "overview instruction")
        self.assertIn("SCG (CES: 43.9 – อันดับ 2)", content)
        self.assertIn("PTT (CES: 53.3 – อันดับ 1) ⭐", content)
        self.assertIn("CP (CES: 36.2 – อันดับ 3)", content)
        self.assertLess(content.index("[SCG]"), content.index("[PTT]"))
        self.assertLess(content.index("[PTT]"), content.index("[CP]"))
        self.assertIn("SCG thematic evidence", content)
        self.assertIn("Pillar: ESG Branding", content)

    def test_validation_reports_missing_score_and_key_thematic(self):
        error = overview_ces_validation_error(
            {"SCG": ces_row(50), "PTT": ces_row(40), "CP": None},
            {"SCG": "ok", "PTT": None, "CP": "ok"},
        )

        self.assertIn("CES Score ขาด CP", error)
        self.assertIn("Key Thematic ขาด PTT", error)


if __name__ == "__main__":
    unittest.main()
