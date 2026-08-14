import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULTS = {
    "model": "gpt-5.6-luna",
    "base_url": "https://api.openai.com/v1",
    "max_completion_tokens": 4000,
    "pricing_usd_per_million_tokens": {},
    "send_images": True,
    "image_slots": [],
    "pillars": ["ESG Branding", "Business Branding", "Employer Branding"],
    "sections": [],
}


def load_config(path=None):
    p = Path(path) if path else CONFIG_PATH
    if not p.exists():
        return DEFAULTS.copy()
    raw = json.loads(p.read_text(encoding="utf-8"))
    cfg = {**DEFAULTS, **raw}
    cfg.setdefault("image_slots", [])
    cfg.setdefault("sections", [])
    return cfg
