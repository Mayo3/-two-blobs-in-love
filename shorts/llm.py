"""Free LLM access. In GitHub Actions, GitHub Models works with the built-in token
(no key, no cost). Locally or as a fallback, Google Gemini's free tier works with a key.
"""
import json
import os

import requests

GITHUB_MODEL = os.environ.get("GITHUB_MODEL", "openai/gpt-4.1")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")


def provider():
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("GITHUB_TOKEN"):
        return "github"
    raise SystemExit("No free LLM configured: set GITHUB_TOKEN (GitHub Models) or GEMINI_API_KEY")


def chat_json(system, user, temperature=0.8):
    """Send a prompt and return the model's reply parsed as JSON."""
    if provider() == "gemini":
        r = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent",
            params={"key": os.environ["GEMINI_API_KEY"]},
            json={
                "systemInstruction": {"parts": [{"text": system}]},
                "contents": [{"role": "user", "parts": [{"text": user}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": temperature},
            },
            timeout=120,
        )
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    else:
        r = requests.post(
            "https://models.github.ai/inference/chat/completions",
            headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"},
            json={
                "model": GITHUB_MODEL,
                "temperature": temperature,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            },
            timeout=120,
        )
        r.raise_for_status()
        text = r.json()["choices"][0]["message"]["content"]
    return json.loads(text)
