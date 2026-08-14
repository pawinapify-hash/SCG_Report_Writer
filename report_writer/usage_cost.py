USAGE_KEYS = (
    "prompt_tokens",
    "completion_tokens",
    "cached_tokens",
    "cache_write_tokens",
)


def empty_usage():
    return {key: 0 for key in USAGE_KEYS}


def add_usage(total, usage):
    if not usage:
        return total

    for key in ("prompt_tokens", "completion_tokens"):
        value = usage.get(key)
        if isinstance(value, int):
            total[key] = total.get(key, 0) + value

    prompt_details = usage.get("prompt_tokens_details") or {}
    for key in ("cached_tokens", "cache_write_tokens"):
        value = prompt_details.get(key)
        if isinstance(value, int):
            total[key] = total.get(key, 0) + value

    return total


def estimate_usage_cost(usage, model, pricing_by_model):
    pricing = (pricing_by_model or {}).get(model)
    if not usage or not pricing:
        return None

    prompt_tokens = max(int(usage.get("prompt_tokens", 0) or 0), 0)
    completion_tokens = max(int(usage.get("completion_tokens", 0) or 0), 0)
    cached_tokens = max(int(usage.get("cached_tokens", 0) or 0), 0)
    cache_write_tokens = max(int(usage.get("cache_write_tokens", 0) or 0), 0)
    uncached_tokens = max(prompt_tokens - cached_tokens - cache_write_tokens, 0)

    cost = (
        uncached_tokens * float(pricing["input"])
        + cached_tokens * float(pricing.get("cached_input", pricing["input"]))
        + cache_write_tokens * float(pricing.get("cache_write_input", pricing["input"]))
        + completion_tokens * float(pricing["output"])
    ) / 1_000_000
    return cost


def usage_summary(usage, model, pricing_by_model):
    tokens = (
        f"Tokens: {usage.get('prompt_tokens', 0)} prompt + "
        f"{usage.get('completion_tokens', 0)} completion"
    )
    cost = estimate_usage_cost(usage, model, pricing_by_model)
    if cost is None:
        return f"{tokens} | Estimated cost: unavailable for {model}"
    return f"{tokens} | Estimated cost: ${cost:.6f}"
