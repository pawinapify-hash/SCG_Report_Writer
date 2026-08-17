import math

from report_writer.key_thematic import BRANDS


def _number(row, field):
    if row is None:
        return None
    value = row.get(field)
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number):
        return None
    return number


def format_millions(value, signed=False):
    millions = float(value) / 1_000_000
    rounded = round(millions, 1)
    if rounded == 0:
        rounded = 0.0
    text = f"{rounded:.1f}".removesuffix(".0")
    if signed and rounded > 0:
        text = "+" + text
    return text + "M"


def overview_pre_validation_error(pre_rows, top_pri_outputs):
    missing_values = [
        brand for brand in BRANDS
        if (
            _number(pre_rows.get(brand), "PRI") is None
            or _number(pre_rows.get(brand), "PRI Growth") is None
        )
    ]
    missing_top_pri = [
        brand for brand in BRANDS
        if not top_pri_outputs.get(brand)
    ]
    issues = []
    if missing_values:
        issues.append("PRI/PRI Growth ขาด " + ", ".join(missing_values))
    if missing_top_pri:
        issues.append("Top PRI Content ขาด " + ", ".join(missing_top_pri))
    if not issues:
        return None
    return "ข้อมูลไม่ครบ: " + "; ".join(issues)


def build_overview_pre_messages(pillar, pre_rows, top_pri_outputs, instruction=""):
    validation_error = overview_pre_validation_error(pre_rows, top_pri_outputs)
    if validation_error:
        raise ValueError(validation_error)

    blocks = []
    for brand in BRANDS:
        total = _number(pre_rows[brand], "PRI")
        growth = _number(pre_rows[brand], "PRI Growth")
        blocks.append(
            f"[ข้อมูลของ {brand}]\n"
            f"PRI รวม: {format_millions(total)}\n"
            f"PRI Growth: {format_millions(growth, signed=True)}\n"
            f"ข้อมูลประเด็นการสื่อสาร:\n{top_pri_outputs[brand]}"
        )

    user_content = (
        "=== PRE Overview ===\n"
        f"Pillar: {pillar}\n\n"
        "ใช้ข้อมูลของ SCG, PTT และ CP ด้านล่างเพื่อเขียนผลลัพธ์ตาม instruction\n\n"
        + "\n\n".join(blocks)
        + "\n\nสำคัญ: ใช้เฉพาะข้อมูลของ Pillar นี้ ห้ามนำข้อมูลจาก Pillar อื่นมาปะปน"
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]
