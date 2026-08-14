import unittest

from report_writer.top_pri_content import build_top_pri_messages, group_top_pri_posts


class TopPriContentMessageTests(unittest.TestCase):
    def test_grouping_keeps_brand_and_pillar_isolated_and_merges_same_combo(self):
        results = [
            {"kind": "PRE", "pillar": "ESG Branding", "brand": "SCG", "posts": ["one"]},
            {"kind": "PRE", "pillar": "ESG Branding", "brand": "SCG", "posts": ["two"]},
            {"kind": "PRE", "pillar": "ESG Branding", "brand": "PTT", "posts": ["ptt"]},
            {"kind": "PRE", "pillar": "Sport", "brand": "SCG", "posts": ["sport"]},
            {"kind": "CES", "pillar": "ESG Branding", "brand": "SCG", "posts": ["ces"]},
        ]

        grouped = group_top_pri_posts(results, ["ESG Branding"])

        self.assertEqual(grouped[("ESG Branding", "SCG")], ["one", "two"])
        self.assertEqual(grouped[("ESG Branding", "PTT")], ["ptt"])
        self.assertNotIn(("Sport", "SCG"), grouped)
        self.assertNotIn("ces", grouped[("ESG Branding", "SCG")])

    def test_message_contains_three_brand_scores_and_target_posts_only(self):
        rows = {
            "SCG": {"PRI": 62_000_000, "PRI Growth": -1, "Standard Rate Card": 10,
                    "Standard Rate Card Growth": 1, "PRE": 2.3, "PRE Growth": 0.1},
            "PTT": {"PRI": 36_000_000, "PRI Growth": 2, "Standard Rate Card": 20,
                    "Standard Rate Card Growth": 2, "PRE": 2.2, "PRE Growth": -0.1},
            "CP": {"PRI": 60_000_000, "PRI Growth": 3, "Standard Rate Card": 30,
                   "Standard Rate Card Growth": 3, "PRE": 2.1, "PRE Growth": 0},
        }
        posts = [{
            "tag": "Thought Leadership",
            "publisher": "Example News",
            "caption": "SCG target caption",
            "metrics": {"pri": 5_000_000, "pre": 2.4, "engagement": 100},
            "image_description": "SCG target image",
        }]

        messages = build_top_pri_messages(
            "ESG Branding", "SCG", rows, posts, instruction="instruction"
        )
        content = messages[1]["content"]

        self.assertEqual(messages[0], {"role": "system", "content": "instruction"})
        self.assertIn("SCG: PRI: 62,000,000", content)
        self.assertIn("PTT: PRI: 36,000,000", content)
        self.assertIn("CP: PRI: 60,000,000", content)
        self.assertIn("SCG target caption", content)
        self.assertIn("Example News", content)
        self.assertIn("Pillar: ESG Branding", content)
        self.assertIn("Brand ที่วิเคราะห์: SCG", content)

    def test_message_does_not_invent_missing_brand_or_external_posts(self):
        messages = build_top_pri_messages(
            "Business Branding",
            "PTT",
            {"SCG": None, "PTT": {"PRI": 10}, "CP": None},
            [{"caption": "PTT only", "metrics": {}}],
        )
        content = messages[1]["content"]

        self.assertIn("PTT: PRI: 10", content)
        self.assertNotIn("SCG: PRI:", content)
        self.assertNotIn("CP: PRI:", content)
        self.assertNotIn("Other Pillar", content)


if __name__ == "__main__":
    unittest.main()
