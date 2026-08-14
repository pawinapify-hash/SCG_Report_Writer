import math

import requests

from report_writer.ces_data import CES_METRICS

BRANDS = ["SCG", "PTT", "CP"]


def _fmt_num(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        if math.isnan(v):
            return "-"
        if v.is_integer():
            return str(int(v))
    return str(v)


def _fmt_growth(v):
    if v is None:
        return "-"
    if isinstance(v, float) and math.isnan(v):
        return "-"
    try:
        n = float(v)
        return f"+{n}" if n > 0 else str(n)
    except (TypeError, ValueError):
        return str(v)


def build_ces_score_text(row):
    lines = []
    for m in CES_METRICS:
        score = _fmt_num(row.get(m))
        growth = _fmt_growth(row.get(m + " Growth"))
        lines.append(f"{m}: {score} (Growth {growth})")
    return "\n".join(lines)


def build_posts_text(posts):
    blocks = []
    for i, p in enumerate(posts, 1):
        tag = p.get("tag") or "-"
        m = p.get("metrics") or {}
        img = p.get("image_description") or "-"
        if p.get("kind") == "pre":
            metric_line = (
                f"PRI: {_fmt_num(m.get('pri'))} | PRE: {_fmt_num(m.get('pre'))} | "
                f"Engagement: {_fmt_num(m.get('engagement'))}"
            )
        else:
            metric_line = (
                f"Engagement: {_fmt_num(m.get('engagement'))} | "
                f"Like: {_fmt_num(m.get('like'))} | Comment: {_fmt_num(m.get('comment'))} | "
                f"Share: {_fmt_num(m.get('share'))}"
            )
        blocks.append(
            f"[โพสต์ {i}]\n"
            f"Tag: {tag}\n"
            f"Caption: {p.get('caption', '')}\n"
            f"{metric_line}\n"
            f"Image: {img}"
        )
    return "\n\n".join(blocks)


def build_ces_comparison_text(ces_rows):
    lines = []
    for brand in BRANDS:
        row = ces_rows.get(brand)
        if row is None:
            continue
        parts = []
        for m in CES_METRICS:
            parts.append(f"{m} {_fmt_num(row.get(m))} (Growth {_fmt_growth(row.get(m + ' Growth'))})")
        lines.append(f"{brand}: " + " | ".join(parts))
    return "\n".join(lines)


def build_key_thematic_messages(pillar, brand, ces_rows, posts, instruction=""):
    score_text = build_ces_comparison_text(ces_rows)
    posts_text = build_posts_text(posts)

    user_content = (
        f"=== Key Thematic Analysis ===\n"
        f"Pillar: {pillar}\n"
        f"Brand ที่วิเคราะห์: {brand}\n\n"
        f"CES Score ของทั้ง 3 แบรนด์ใน Pillar นี้ (สำหรับเปรียบเทียบ):\n"
        f"{score_text}\n\n"
        f"โพสต์ของ {brand} ใน {pillar} ({len(posts)} โพสต์):\n"
        f"{posts_text}"
    )
    return [
        {"role": "system", "content": instruction},
        {"role": "user", "content": user_content},
    ]


def chat_text(messages, api_key, model="gpt-4o", base_url="https://api.openai.com/v1",
              temperature=0.2, max_tokens=4000):
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=300)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"], data.get("usage")
