import unittest

import pandas as pd

from report_writer.pri_mri import build_pri_mri_messages, prepare_pri_mri_rows


class PriMriTests(unittest.TestCase):
    def test_prepare_rows_requires_all_columns(self):
        frame = pd.DataFrame({"Content": ["a"], "Username": ["u"]})

        rows, error = prepare_pri_mri_rows("SCG_ESG Branding", frame)

        self.assertIsNone(rows)
        self.assertIn("คอลัมน์ไม่ครบ", error)

    def test_prepare_rows_skips_sheet_when_any_required_data_missing(self):
        frame = pd.DataFrame(
            {
                "Content": ["first", ""],
                "Username": ["u1", "u2"],
                "PRI": [100, 200],
                "Engagement": [10, 20],
            }
        )

        rows, error = prepare_pri_mri_rows("SCG_ESG Branding", frame)

        self.assertIsNone(rows)
        self.assertIn("พบข้อมูลไม่ครบ", error)

    def test_prepare_rows_truncates_content_and_marks_performance(self):
        frame = pd.DataFrame(
            {
                "Content": ["x" * 300] + ["ok"] * 10,
                "Username": ["user"] * 11,
                "PRI": list(range(11)),
                "Engagement": list(range(11)),
            }
        )

        rows, error = prepare_pri_mri_rows("SCG_ESG Branding", frame)

        self.assertIsNone(error)
        self.assertEqual(len(rows[0]["Content"]), 250)
        self.assertEqual(rows[0]["performance"], "High Performing")
        self.assertEqual(rows[10]["performance"], "Low Performing")

    def test_prepare_rows_uses_only_first_100_rows(self):
        frame = pd.DataFrame(
            {
                "Content": [f"post {index}" for index in range(120)],
                "Username": ["user"] * 120,
                "PRI": list(range(120)),
                "Engagement": list(range(120)),
            }
        )

        rows, error = prepare_pri_mri_rows("SCG_ESG Branding", frame)

        self.assertIsNone(error)
        self.assertEqual(len(rows), 100)
        self.assertEqual(rows[0]["row_no"], 1)
        self.assertEqual(rows[-1]["row_no"], 100)

    def test_message_includes_only_expected_raw_fields(self):
        rows = [
            {
                "row_no": 1,
                "performance": "High Performing",
                "Content": "content text",
                "Username": "example_user",
                "PRI": 123,
                "Engagement": 45,
            }
        ]

        messages = build_pri_mri_messages("SCG_ESG Branding", rows, instruction="instruction")
        content = messages[1]["content"]

        self.assertEqual(messages[0], {"role": "system", "content": "instruction"})
        self.assertIn("Content: content text", content)
        self.assertIn("Username: example_user", content)
        self.assertIn("PRI: 123", content)
        self.assertIn("Engagement: 45", content)
        self.assertNotIn("Ratecard", content)
        self.assertNotIn("Sentiment", content)


if __name__ == "__main__":
    unittest.main()