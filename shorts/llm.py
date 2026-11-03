"""Free LLM access through Google Gemini's free tier (needs GEMINI_API_KEY).
GitHub Models used to be the keyless option but was retired on 2026-07-30.
"""
import json
import os
import time

import requests

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
# Tried when the main model gives no answer; it has its own, larger free daily quota.
GEMINI_FALLBACK = os.environ.get("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite")


def chat_json(system, user, temperature=0.8):
    """Send a prompt and return the model's reply parsed as JSON."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise SystemExit("No free LLM configured: set GEMINI_API_KEY (free at https://aistudio.google.com/apikey)")
    return json.loads(gemini_chat(key, system, user, temperature))


def gemini_chat(key, system, user, temperature):
    """The free tier now and then answers with a rate limit or an overload: retry a few
    times, then try the fallback model, and fail with what the service actually said."""
    problems = []
    for model in (GEMINI_MODEL, GEMINI_FALLBACK):
        for attempt in range(3):
            if attempt:
                time.sleep(20 * attempt)
            try:
                r = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": key},
                    json={
                        "systemInstruction": {"parts": [{"text": system}]},
                        "contents": [{"role": "user", "parts": [{"text": user}]}],
                        "generationConfig": {"responseMimeType": "application/json", "temperature": temperature},
                    },
                    timeout=120,
                )
            except requests.RequestException as e:
                problems.append(f"{model}: {e}")
                continue
            try:
                text = r.json()["candidates"][0]["content"]["parts"][0]["text"] if r.ok else None
            except (ValueError, KeyError, IndexError, TypeError):
                text = None
            if text:
                return text
            problems.append(f"{model}: HTTP {r.status_code} {r.text[:300]!r}")
            print(f"Gemini: {problems[-1]}")
            if r.status_code in (400, 401, 403):
                break   # bad key or request; retrying won't help
    raise SystemExit("Gemini gave no answer:\n" + "\n".join(problems))
