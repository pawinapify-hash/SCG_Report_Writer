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


def calculate_pri_comparison(pre_rows):
    values = {
        brand: _number(pre_rows.get(brand), "PRI")
        for brand in BRANDS
    }
    valid_values = [value for value in values.values() if value is not None]
    if not valid_values:
        return {}
    highest = max(valid_values)
    return {
        brand: {
            "pri": value,
            "is_highest": value == highest,
        }
        for brand, value in values.items()
        if value is not None
    }


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


def _movement_text(total, growth):
    total_text = format_millions(total)
    growth_text = format_millions(growth, signed=True)
    if growth > 0:
        return f"มูลค่าสื่อเพิ่มขึ้น {growth_text} (มูลค่ารวม {total_text})"
    if growth < 0:
        return f"มูลค่าสื่อลดลง {growth_text} (มูลค่ารวม {total_text})"
    return f"มูลค่าสื่อทรงตัว {growth_text} (มูลค่ารวม {total_text})"


def build_overview_pre_messages(pillar, pre_rows, top_pri_outputs, instruction=""):
    validation_error = overview_pre_validation_error(pre_rows, top_pri_outputs)
    if validation_error:
        raise ValueError(validation_error)

    comparison = calculate_pri_comparison(pre_rows)
    blocks = []
    for brand in BRANDS:
        total = comparison[brand]["pri"]
        growth = _number(pre_rows[brand], "PRI Growth")
        comparison_text = "สูงสุดในกลุ่ม" if comparison[brand]["is_highest"] else "ไม่ใช่ค่าสูงสุดในกลุ่ม"
        blocks.append(
            f"[{brand}]\n"
            f"ชื่อแบรนด์บังคับสำหรับบรรทัดแรก: {brand}\n"
            f"ข้อความบังคับสำหรับเปิดเนื้อหา: {_movement_text(total, growth)}\n"
            f"สถานะเปรียบเทียบ PRI: {comparison_text}\n"
            f"คำตอบ Top PRI Content:\n{top_pri_outputs[brand]}"
        )

    user_content = (
        "=== PRE Overview ===\n"
        f"Pillar: {pillar}\n\n"
        "เขียนผลลัพธ์ 3 ส่วนตามลำดับ SCG, PTT, CP ด้านล่าง "
        "แต่ละส่วนต้องมีชื่อแบรนด์อยู่บรรทัดแรก แล้วตามด้วยหนึ่งย่อหน้า "
        "โดยคัดลอกข้อความบังคับสำหรับเปิดเนื้อหาให้ตรงทุกตัวอักษร\n\n"
        + "\n\n".join(blocks)
        + "\n\nสำคัญ: ใช้เฉพาะข้อมูลของ Pillar นี้ ห้ามนำข้อมูลจาก Pillar อื่นมาปะปน"
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]
