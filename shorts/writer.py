"""Writes a script for one fact with a free LLM, then holds it to the same bar as the
hand-written samples. A script that keeps failing the checks is never rendered.
"""
import json
import os

from .captions import PALETTES
from .cartoon.director import ACTIONS, describe_actions
from .cartoon.scenes import Scene
from .llm import chat_json
from .produce import ROOT
from .style import BANNED_PHRASES, MAX_HOOK_WORDS, MAX_SENTENCE_WORDS, MAX_WORDS, MIN_WORDS, check_script

FORMATS = {
    "story": "Tell how the study was done, like a short story, then land the finding and what it means for the viewer.",
    "myth-vs-fact": "Open with the popular belief stated confidently, then overturn it with the finding.",
    "experiment": "Walk through the experiment step by step (what researchers did, what happened), then the twist.",
    "try-this": "Turn the finding into one small thing the viewer can try with their partner today.",
    "quiz": "Open by making the viewer guess (e.g. which couples..., what happened when...), then reveal.",
}

SYSTEM = f"""You write scripts for "Two Blobs in Love", a TikTok channel of science-backed facts about couples.
Each video is narrated over a cartoon of two cute blob characters who act out every line.

Voice: a warm, clever friend telling you something surprising over coffee. Plain spoken English.
Specific and concrete. A little playful. Never preachy, never salesy, never generic.

Audience: mostly 18 to 34, dating or in their first serious relationships. Talk to them about "you two"
and "your partner". Don't assume they are married: say "married couples", "newlyweds", "husband" or
"divorce" only when describing who was studied, then bring it straight back to the viewer.
Light and curious beats heavy: playful questions about love get watched far longer than warnings about breakups.

Hard rules:
- Use ONLY the fact you are given. Every number you say must appear in the fact. No other statistics.
- Never invent details about the study (no made-up participant counts, places, or quotes).
- {MIN_WORDS}-{MAX_WORDS} words in total, 5-8 lines. Short is the point: every line must earn its place. Each line is one or two short spoken sentences, at most {MAX_SENTENCE_WORDS} words per sentence.
- Line 1 is the hook, at most {MAX_HOOK_WORDS} words. It is shown on screen while it is spoken, alone, so it must work on its own and make someone stop scrolling.
  Open a question the video then answers, so viewers stay to find out: a yes-or-no question about something people
  believe or wonder about ("Do couples really start to *look alike*?", "Can eye contact make you *fall* for someone?"),
  or a belief stated as fact that the video will overturn. Never give the answer away in line 1.
  Not a lazy question like "Have you ever..." or "Do you...".
- Write numbers as digits and spell out "percent" (e.g. "86 percent") so the narrator reads them right.
- Mark 1-4 key words or numbers with *asterisks* (they get highlighted).
- The last line is a question the viewer can answer in a word or two (yes or no, this or that, A or B), so they reply in the comments. Never "follow for more" or "comment below".
- At most one exclamation mark. No emojis. No hashtags in the script.
- Never use these words or phrases: {", ".join(BANNED_PHRASES)}.

Cartoon: for every line pick an action (or a list of 2-3 actions that split the line) from this list.
Pick actions that literally show what the line says. Use "name:arg" only where the description mentions an arg.
{describe_actions()}

Palettes (caption highlight colours): {", ".join(PALETTES)}.

Reply with JSON only:
{{"title": "...", "scene": "...", "palette": "...", "lines": ["..."], "beats": ["action" or ["action", "action"], ...], "caption": "..."}}
- "title": under 40 characters, a punchy name for the video (used in notifications and the history).
- "beats" has exactly one entry per line.
- "caption": the TikTok caption, one or two natural sentences (under 150 characters), no hashtags.
"""


def examples():
    samples = json.load(open(os.path.join(ROOT, "samples", "scripts.json"), encoding="utf-8"))
    keep = ("title", "scene", "palette", "lines", "beats")
    return "\n\n".join(
        f"Example ({s['format']}):\n" + json.dumps({k: s[k] for k in keep}, ensure_ascii=False) for s in samples
    )


def validate(script, fact, scenes=Scene.kinds):
    problems = check_script(script, fact)
    lines, beats = script.get("lines", []), script.get("beats", [])
    if not 5 <= len(lines) <= 8:
        problems.append(f"{len(lines)} lines (want 5-8)")
    if len(beats) != len(lines):
        problems.append(f"{len(beats)} beats for {len(lines)} lines")
    for b in beats:
        for part in b if isinstance(b, list) else [b]:
            if not isinstance(part, str) or part.partition(":")[0] not in ACTIONS:
                problems.append(f"unknown action '{part}'")
    if script.get("scene") not in scenes:
        problems.append(f"scene '{script.get('scene')}' is not one of: {', '.join(scenes)}")
    if script.get("palette") not in PALETTES:
        problems.append(f"unknown palette '{script.get('palette')}'")
    if not script.get("title") or len(script["title"]) > 45:
        problems.append("title missing or too long")
    if "#" in script.get("caption", ""):
        problems.append("caption contains hashtags")
    return problems


def write_script(fact, fmt, scenes=Scene.kinds, tries=3):
    """Return a validated script dict, or raise after `tries` failed attempts."""
    user = (
        f"Fact: {fact['claim']}\nSource: {fact['source']}\n\n"
        f"Format: {fmt} — {FORMATS[fmt]}\n\n"
        f"Scene: pick the one of these that fits the story best: {', '.join(scenes)}.\n\n"
        f"{examples()}\n\nWrite the new script."
    )
    problems = []
    for attempt in range(tries):
        prompt = user if not problems else (
            f"{user}\n\nYour previous attempt:\n{json.dumps(script, ensure_ascii=False)}\n\n"
            f"It failed these checks, fix every one:\n- " + "\n- ".join(problems)
        )
        script = chat_json(SYSTEM, prompt, temperature=0.8 if attempt == 0 else 0.6)
        script["fact"], script["format"] = fact["id"], fmt
        problems = validate(script, fact, scenes)
        if not problems:
            return script
        print(f"attempt {attempt + 1} rejected: {problems}")
    raise RuntimeError(f"no acceptable script after {tries} tries: {problems}")
