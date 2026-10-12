import io
import math

import pandas as pd


REQUIRED_COLUMNS = ["Content", "Username", "PRI", "Engagement"]
MAX_CONTENT_CHARS = 250
MAX_ROWS_PER_SHEET = 100


def parse_sheet_context(sheet_name):
    if not sheet_name:
        return None, None
    parts = str(sheet_name).split("_", 1)
    if len(parts) != 2:
        return None, str(sheet_name)
    brand = parts[0].strip() or None
    pillar = parts[1].strip() or None
    return brand, pillar


def load_top_pri_content_workbook(file_bytes):
    return pd.read_excel(io.BytesIO(file_bytes), sheet_name=None)


def _is_missing(value):
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _text(value):
    if value is None:
        return ""
    return str(value).strip()


def _truncate_content(text, max_chars=MAX_CONTENT_CHARS):
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def prepare_pri_mri_rows(sheet_name, data_frame):
    if data_frame is None:
        return None, f"ข้าม {sheet_name}: ไม่พบข้อมูลชีท"

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in data_frame.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        return None, f"ข้าม {sheet_name}: คอลัมน์ไม่ครบ ({missing_text})"

    rows = data_frame.head(MAX_ROWS_PER_SHEET)[REQUIRED_COLUMNS].copy()
    if rows.empty:
        return None, f"ข้าม {sheet_name}: ไม่มีข้อมูล"

    invalid_rows = []
    prepared_rows = []
    for row_index, row in rows.iterrows():
        content = _text(row.get("Content"))
        username = _text(row.get("Username"))
        pri = row.get("PRI")
        engagement = row.get("Engagement")

        if _is_missing(content) or _is_missing(username) or _is_missing(pri) or _is_missing(engagement):
            invalid_rows.append(row_index + 1)
            continue

        prepared_rows.append({
            "row_no": row_index + 1,
            "performance": "High Performing" if (row_index + 1) <= 10 else "Low Performing",
            "Content": _truncate_content(content),
            "Username": username,
            "PRI": pri,
            "Engagement": engagement,
        })

    if invalid_rows:
        first_rows = ", ".join(str(number) for number in invalid_rows[:5])
        return None, f"ข้าม {sheet_name}: พบข้อมูลไม่ครบในแถว {first_rows}"

    return prepared_rows, None


def build_pri_mri_messages(sheet_name, prepared_rows, instruction=""):
    brand, pillar = parse_sheet_context(sheet_name)
    brand_text = brand or "-"
    pillar_text = pillar or "-"

    blocks = []
    for row in prepared_rows:
        blocks.append(
            f"[โพสต์ {row['row_no']}]\n"
            f"Performance: {row['performance']}\n"
            f"Content: {row['Content']}\n"
            f"Username: {row['Username']}\n"
            f"PRI: {row['PRI']}\n"
            f"Engagement: {row['Engagement']}"
        )

    user_content = (
        "=== PRI MRI Analysis ===\n"
        f"Sheet: {sheet_name}\n"
        f"Brand: {brand_text}\n"
        f"Pillar: {pillar_text}\n"
        "ข้อมูลนี้ใช้เฉพาะ Brand/Pillar ของชีทนี้เท่านั้น\n\n"
        "ข้อมูลดิบที่ส่งให้วิเคราะห์ (เฉพาะคอลัมน์ Content, Username, PRI, Engagement):\n"
        + "\n\n".join(blocks)
    )

    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]