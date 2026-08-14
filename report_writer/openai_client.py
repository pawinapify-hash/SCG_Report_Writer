import base64
import mimetypes

import requests


def dataframe_to_csv(df):
    if df is None or df.empty:
        return "(no excel data)"
    return df.to_csv(index=False)


def _encode_image(data, filename=None):
    mime = "image/png"
    if filename:
        guessed = mimetypes.guess_type(filename)[0]
        if guessed:
            mime = guessed
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


def build_messages(prompt, csv_text, images):
    content = [{"type": "text", "text": csv_text}]
    for filename, data in images:
        content.append({"type": "image_url", "image_url": {"url": _encode_image(data, filename)}})

    user_content = content if images else csv_text
    return [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_content},
    ]


def chat(messages, api_key, model="gpt-5.6-luna", base_url="https://api.openai.com/v1",
         temperature=0.2, max_tokens=4000):
    url = base_url.rstrip("/") + "/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_completion_tokens": max_tokens,
        "stream": False,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
