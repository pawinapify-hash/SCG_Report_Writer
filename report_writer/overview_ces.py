import math

from report_writer.key_thematic import BRANDS, build_ces_score_text


def _ces_score(row):
    if row is None:
        return None
    value = row.get("CES Score")
    if value is None:
        return None
    try:
        score = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(score):
        return None
    return score


def calculate_ces_rankings(ces_rows):
    scores = {
        brand: _ces_score(ces_rows.get(brand))
        for brand in BRANDS
    }
    valid_scores = [score for score in scores.values() if score is not None]
    if not valid_scores:
        return {}

    highest_score = max(valid_scores)
    rankings = {}
    for brand, score in scores.items():
        if score is None:
            continue
        rankings[brand] = {
            "score": score,
            "rank": 1 + sum(other > score for other in valid_scores),
            "is_top": score == highest_score,
        }
    return rankings


def overview_ces_validation_error(ces_rows, key_thematic_outputs):
    missing_scores = [
        brand for brand in BRANDS
        if _ces_score(ces_rows.get(brand)) is None
    ]
    missing_key_thematics = [
        brand for brand in BRANDS
        if not key_thematic_outputs.get(brand)
    ]
    issues = []
    if missing_scores:
        issues.append("CES Score ขาด " + ", ".join(missing_scores))
    if missing_key_thematics:
        issues.append("Key Thematic ขาด " + ", ".join(missing_key_thematics))
    if not issues:
        return None
    return "ข้อมูลไม่ครบ: " + "; ".join(issues)


def _required_prefix(brand, ranking):
    score = f"{ranking['score']:.1f}"
    star = " ⭐" if ranking["is_top"] else ""
    return f"{brand} (CES: {score} – อันดับ {ranking['rank']}){star}"


def build_overview_ces_messages(
    pillar,
    ces_rows,
    key_thematic_outputs,
    instruction="",
):
    validation_error = overview_ces_validation_error(ces_rows, key_thematic_outputs)
    if validation_error:
        raise ValueError(validation_error)

    rankings = calculate_ces_rankings(ces_rows)
    blocks = []
    for brand in BRANDS:
        blocks.append(
            f"[{brand}]\n"
            f"ข้อความบังคับสำหรับเปิดย่อหน้า: {_required_prefix(brand, rankings[brand])}\n"
            f"คะแนน CES และ Growth:\n{build_ces_score_text(ces_rows[brand])}\n"
            f"คำตอบ Key Thematic:\n{key_thematic_outputs[brand]}"
        )

    user_content = (
        "=== Overview CES ===\n"
        f"Pillar: {pillar}\n\n"
        "เขียนผลลัพธ์ 3 ย่อหน้าตามลำดับ SCG, PTT, CP ด้านล่าง "
        "และคัดลอกข้อความบังคับสำหรับเปิดย่อหน้าให้ตรงทุกตัวอักษร\n\n"
        + "\n\n".join(blocks)
        + "\n\nสำคัญ: ใช้เฉพาะข้อมูลของ Pillar นี้ ห้ามนำข้อมูลจาก Pillar อื่นมาปะปน"
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]
