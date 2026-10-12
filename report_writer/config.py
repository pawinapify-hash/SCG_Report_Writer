import json
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config.json"

DEFAULTS = {
    "model": "gpt-5.6-luna",
    "extract_model": "gpt-5.6-luna",
    "analysis_model": "gpt-5.6-luna",
    "base_url": "https://api.openai.com/v1",
    "max_completion_tokens": 4000,
    "pricing_usd_per_million_tokens": {},
    "model_pricing_usd_per_million_tokens": [],
    "send_images": True,
    "image_slots": [],
    "pillars": ["ESG Branding", "Business Branding", "Employer Branding"],
    "sections": [],
    "analysis_parallel_enabled": True,
    "analysis_parallel_workers": 3,
    "extract_parallel_enabled": True,
    "extract_parallel_workers": 2,
}


def _pricing_list_to_map(model_pricing_list):
    pricing_map = {}
    for item in model_pricing_list or []:
        model_name = (item or {}).get("model")
        if not model_name:
            continue
        pricing_map[model_name] = {
            "input": item.get("input", 0),
            "cached_input": item.get("cached_input", item.get("input", 0)),
            "cache_write_input": item.get("cache_write_input", item.get("input", 0)),
            "output": item.get("output", 0),
        }
    return pricing_map


def load_config(path=None):
    p = Path(path) if path else CONFIG_PATH
    if not p.exists():
        return DEFAULTS.copy()

    raw = json.loads(p.read_text(encoding="utf-8-sig"))
    cfg = {**DEFAULTS, **raw}
    cfg.setdefault("image_slots", [])
    cfg.setdefault("sections", [])

    base_model = cfg.get("model", DEFAULTS["model"])
    if not raw.get("extract_model"):
        cfg["extract_model"] = base_model
    if not raw.get("analysis_model"):
        cfg["analysis_model"] = base_model

    pricing_from_list = _pricing_list_to_map(cfg.get("model_pricing_usd_per_million_tokens", []))
    if pricing_from_list:
        cfg["pricing_usd_per_million_tokens"] = pricing_from_list
    return cfg
