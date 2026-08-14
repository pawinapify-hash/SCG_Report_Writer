import math

from report_writer.key_thematic import BRANDS


PRE_SCORE_FIELDS = [
    "PRI",
    "PRI Growth",
    "Standard Rate Card",
    "Standard Rate Card Growth",
    "PRE",
    "PRE Growth",
]


def group_top_pri_posts(results, allowed_pillars):
    grouped = {}
    for result in results:
        if result.get("kind") != "PRE":
            continue
        pillar = result.get("pillar")
        brand = result.get("brand")
        if pillar not in allowed_pillars or brand not in BRANDS:
            continue
        grouped.setdefault((pillar, brand), []).extend(result.get("posts") or [])
    return grouped


def _is_missing(value):
    return value is None or (isinstance(value, float) and math.isnan(value))


def _fmt_number(value, signed=False):
    if _is_missing(value):
        return "-"
    try:
        number = float(value)
    except (TypeError, ValueError):
        return str(value)

    if number.is_integer():
        text = f"{int(number):,}"
    else:
        text = f"{number:g}"
    if signed and number > 0:
        return f"+{text}"
    return text


def build_pre_comparison_text(pre_rows):
    lines = []
    for brand in BRANDS:
        row = pre_rows.get(brand)
        if row is None:
            continue
        parts = [
            f"PRI: {_fmt_number(row.get('PRI'))}",
            f"PRI Growth: {_fmt_number(row.get('PRI Growth'), signed=True)}",
            f"Standard Rate Card: {_fmt_number(row.get('Standard Rate Card'))}",
            (
                "Standard Rate Card Growth: "
                f"{_fmt_number(row.get('Standard Rate Card Growth'), signed=True)}"
            ),
            f"PRE: {_fmt_number(row.get('PRE'))}",
            f"PRE Growth: {_fmt_number(row.get('PRE Growth'), signed=True)}",
        ]
        lines.append(f"{brand}: " + " | ".join(parts))
    return "\n".join(lines)


def build_top_pri_posts_text(posts):
    blocks = []
    for index, post in enumerate(posts, 1):
        metrics = post.get("metrics") or {}
        blocks.append(
            f"[โพสต์ {index}]\n"
            f"Tag: {post.get('tag') or '-'}\n"
            f"Publisher: {post.get('publisher') or '-'}\n"
            f"Caption: {post.get('caption') or '-'}\n"
            f"PRI: {_fmt_number(metrics.get('pri'))} | "
            f"PRE: {_fmt_number(metrics.get('pre'))} | "
            f"Engagement: {_fmt_number(metrics.get('engagement'))}\n"
            f"Image: {post.get('image_description') or '-'}"
        )
    return "\n\n".join(blocks)


def build_top_pri_messages(pillar, brand, pre_rows, posts, instruction=""):
    comparison_text = build_pre_comparison_text(pre_rows)
    posts_text = build_top_pri_posts_text(posts)
    user_content = (
        "=== Top PRI Content Analysis ===\n"
        f"Pillar: {pillar}\n"
        f"Brand ที่วิเคราะห์: {brand}\n\n"
        "ข้อมูลสรุป PRE/PRI/Standard Rate Card ของทั้ง 3 แบรนด์ "
        "เฉพาะ Pillar นี้ (ใช้เพื่อเปรียบเทียบ):\n"
        f"{comparison_text}\n\n"
        f"Top PRI Posts ของ {brand} เฉพาะใน {pillar} ({len(posts)} โพสต์):\n"
        f"{posts_text}\n\n"
        "สำคัญ: เนื้อหาโพสต์ด้านบนเป็นของ Brand และ Pillar ที่ระบุเท่านั้น "
        "ห้ามนำข้อมูลจาก Brand หรือ Pillar อื่นมาปะปน"
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]
