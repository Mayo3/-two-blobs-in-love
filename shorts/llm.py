"""Free LLM access. In GitHub Actions, GitHub Models works with the built-in token
(no key, no cost). Locally or as a fallback, Google Gemini's free tier works with a key.
"""
import json
import os
import time

import requests

GITHUB_MODEL = os.environ.get("GITHUB_MODEL", "openai/gpt-4.1")
# Tried when the main model gives no answer; it has its own, larger free daily quota.
GITHUB_FALLBACK = os.environ.get("GITHUB_FALLBACK_MODEL", "openai/gpt-4.1-mini")
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
        text = github_chat(system, user, temperature)
    return json.loads(text)


def github_chat(system, user, temperature):
    """GitHub Models now and then answers with an empty body or a rate limit: retry a few
    times, then try the fallback model, and fail with what the service actually said."""
    problems = []
    for model in (GITHUB_MODEL, GITHUB_FALLBACK):
        for attempt in range(3):
            if attempt:
                time.sleep(20 * attempt)
            try:
                r = requests.post(
                    "https://models.github.ai/inference/chat/completions",
                    headers={"Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}", "Accept": "application/vnd.github+json"},
                    json={
                        "model": model,
                        "temperature": temperature,
                        "response_format": {"type": "json_object"},
                        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                    },
                    timeout=120,
                )
            except requests.RequestException as e:
                problems.append(f"{model}: {e}")
                continue
            try:
                text = r.json()["choices"][0]["message"]["content"] if r.ok else None
            except (ValueError, KeyError, IndexError, TypeError):
                text = None
            if text:
                return text
            problems.append(f"{model}: HTTP {r.status_code} {r.text[:300]!r}")
            print(f"GitHub Models: {problems[-1]}")
            if r.status_code in (401, 403):
                break   # no access to this model; retrying won't help
    raise SystemExit("GitHub Models gave no answer:\n" + "\n".join(problems))
