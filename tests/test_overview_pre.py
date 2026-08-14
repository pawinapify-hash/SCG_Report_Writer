import unittest

from report_writer.overview_pre import (
    build_overview_pre_messages,
    calculate_pri_comparison,
    format_millions,
    overview_pre_validation_error,
)


def pre_row(pri, growth):
    return {"PRI": pri, "PRI Growth": growth}


class OverviewPreTests(unittest.TestCase):
    def test_formats_millions_with_at_most_one_decimal(self):
        self.assertEqual(format_millions(300_000), "0.3M")
        self.assertEqual(format_millions(2_000_000), "2M")
        self.assertEqual(format_millions(82_040_000), "82M")
        self.assertEqual(format_millions(24_000_000, signed=True), "+24M")
        self.assertEqual(format_millions(-28_000_000, signed=True), "-28M")

    def test_comparison_supports_tied_highest_without_stars(self):
        comparison = calculate_pri_comparison({
            "SCG": pre_row(98_000_000, 1),
            "PTT": pre_row(98_000_000, 1),
            "CP": pre_row(67_000_000, 1),
        })

        self.assertTrue(comparison["SCG"]["is_highest"])
        self.assertTrue(comparison["PTT"]["is_highest"])
        self.assertFalse(comparison["CP"]["is_highest"])

    def test_message_uses_fixed_order_m_values_and_top_pri_outputs(self):
        rows = {
            "SCG": pre_row(98_000_000, 24_000_000),
            "PTT": pre_row(55_000_000, 19_000_000),
            "CP": pre_row(67_000_000, -28_000_000),
        }
        outputs = {
            "SCG": "SCG Top PRI evidence",
            "PTT": "PTT Top PRI evidence",
            "CP": "CP Top PRI evidence",
        }

        messages = build_overview_pre_messages(
            "ESG Branding", rows, outputs, instruction="PRE overview instruction"
        )
        content = messages[1]["content"]

        self.assertEqual(messages[0]["content"], "PRE overview instruction")
        self.assertLess(content.index("[SCG]"), content.index("[PTT]"))
        self.assertLess(content.index("[PTT]"), content.index("[CP]"))
        self.assertIn("มูลค่าสื่อเพิ่มขึ้น +24M (มูลค่ารวม 98M)", content)
        self.assertIn("มูลค่าสื่อลดลง -28M (มูลค่ารวม 67M)", content)
        self.assertIn("SCG Top PRI evidence", content)
        self.assertNotIn("⭐", content)

    def test_validation_reports_missing_values_and_top_pri(self):
        error = overview_pre_validation_error(
            {
                "SCG": pre_row(98_000_000, 24_000_000),
                "PTT": pre_row(55_000_000, None),
                "CP": None,
            },
            {"SCG": "ok", "PTT": None, "CP": "ok"},
        )

        self.assertIn("PRI/PRI Growth ขาด PTT, CP", error)
        self.assertIn("Top PRI Content ขาด PTT", error)


if __name__ == "__main__":
    unittest.main()
