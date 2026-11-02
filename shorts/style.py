"""Anti-slop rules. Scripts are checked against these before anything is rendered;
a script that fails is rewritten (by the model) or skipped, never published.
"""
import re

# Phrases that mark a script as generic AI or content-farm filler.
BANNED_PHRASES = [
    "did you know", "here's the thing", "here's the twist", "game changer", "game-changer",
    "delve", "dive in", "let's dive", "unlock", "unleash", "journey", "in today's world",
    "fast-paced world", "in conclusion", "at the end of the day", "it's important to note",
    "studies show", "science says", "research shows", "experts say", "mind-blowing",
    "you won't believe", "will blow your mind", "secret to", "the key to", "hack",
    "follow for more", "like and subscribe", "smash that", "comment below", "stay tuned",
    "tapestry", "testament to", "navigate", "realm", "elevate", "embark", "foster",
    "crucial", "vital", "moreover", "furthermore", "additionally", "ultimately",
    "true love", "soulmate", "relationship goals", "red flag", "green flag",
]

# Things a good script must have.
MIN_WORDS, MAX_WORDS = 70, 135          # about 25-50 seconds of speech
MAX_SENTENCE_WORDS = 22                 # spoken sentences stay short


def plain_text(lines):
    """Script lines without *emphasis* markers."""
    return " ".join(lines).replace("*", "")


def check_script(script, fact):
    """Return a list of problems. Empty list means the script passes."""
    problems = []
    text = plain_text(script["lines"])
    low = text.lower()
    words = text.split()

    for p in BANNED_PHRASES:
        if re.search(r"\b" + re.escape(p) + r"\b", low):
            problems.append(f"banned phrase: '{p}'")
    if not MIN_WORDS <= len(words) <= MAX_WORDS:
        problems.append(f"length {len(words)} words (want {MIN_WORDS}-{MAX_WORDS})")
    for s in re.split(r"(?<=[.!?])\s+", text):
        if len(s.split()) > MAX_SENTENCE_WORDS:
            problems.append(f"sentence too long: '{s[:50]}...'")
    if "!" in text and text.count("!") > 1:
        problems.append("more than one exclamation mark")
    if not any("*" in line for line in script["lines"]):
        problems.append("no *emphasis* marked")
    first = script["lines"][0].replace("*", "")
    if len(first.split()) > 16:
        problems.append("hook (first line) longer than 16 words")
    if first.rstrip().endswith("?") and first.lower().startswith(("have you", "do you", "are you", "ever wonder")):
        problems.append("lazy question hook")
    # Every number in the script must appear in the fact (no invented stats).
    fact_text = fact["claim"].lower()
    for num in re.findall(r"\d+(?:\.\d+)?", text):
        if num not in fact_text and num not in fact["source"]:
            problems.append(f"number '{num}' is not in the source fact")
    return problems
