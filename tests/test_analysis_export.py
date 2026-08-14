import io
import unittest

import pandas as pd

from report_writer.analysis_export import export_analysis_excel


class CombinedAnalysisExportTests(unittest.TestCase):
    def test_export_contains_successful_results_from_all_sections(self):
        results = [
            {
                "section": "CES Key Thematic",
                "title": "CES ESG SCG Key Thematic",
                "output": "Key thematic result",
                "error": None,
            },
            {
                "section": "Top PRI Content",
                "title": "PRE ESG SCG Top PRI Content",
                "output": "Top PRI result",
                "error": None,
            },
            {
                "section": "Top PRI Content",
                "title": "PRE ESG PTT Top PRI Content",
                "output": None,
                "error": "API error",
            },
            {
                "section": "CES Overview",
                "title": "CES ESG Overview",
                "output": "Overview result",
                "error": None,
            },
            {
                "section": "PRE Overview",
                "title": "PRE ESG Overview",
                "output": "PRE overview result",
                "error": None,
            },
        ]

        workbook = export_analysis_excel(results)
        exported = pd.read_excel(io.BytesIO(workbook))

        self.assertEqual(len(exported), 4)
        self.assertEqual(
            exported.iloc[:, 0].tolist(),
            [
                "CES ESG SCG Key Thematic",
                "PRE ESG SCG Top PRI Content",
                "CES ESG Overview",
                "PRE ESG Overview",
            ],
        )
        self.assertEqual(
            exported.iloc[:, 1].tolist(),
            [
                "Key thematic result",
                "Top PRI result",
                "Overview result",
                "PRE overview result",
            ],
        )


if __name__ == "__main__":
    unittest.main()
