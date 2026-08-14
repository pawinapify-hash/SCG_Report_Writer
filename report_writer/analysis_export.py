import io

import pandas as pd


EXPORT_COLUMNS = ["ชื่อหัวข้อ", "คำตอบ"]


def build_analysis_title(category, pillar, brand, analysis_name):
    pillar_name = (pillar or "").removesuffix(" Branding").strip()
    parts = [category, pillar_name, brand, analysis_name]
    return " ".join(str(part).strip() for part in parts if part and str(part).strip())


def analysis_rows(results):
    rows = []
    for result in results:
        if result.get("error") or not result.get("output"):
            continue
        rows.append({
            "ชื่อหัวข้อ": result.get("title", ""),
            "คำตอบ": result["output"],
        })
    return rows


def export_analysis_excel(results):
    rows = analysis_rows(results)
    buffer = io.BytesIO()
    pd.DataFrame(rows, columns=EXPORT_COLUMNS).to_excel(
        buffer,
        index=False,
        sheet_name="Analysis Results",
    )
    return buffer.getvalue()
