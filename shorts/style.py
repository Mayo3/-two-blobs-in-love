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
# The people and places behind a study; the video states the finding, the comment names the source.
STUDY_WORDS = ["researcher", "scientist", "psychologist", "professor", "university", "journal"]

# Things a good script must have.
MIN_WORDS, MAX_WORDS = 52, 70           # about 25-32 seconds: the finding, the odd detail behind it, and what it means (30 words made a 15s video that felt rushed and thin)
MAX_SENTENCE_WORDS = 22                 # spoken sentences stay short
MAX_HOOK_WORDS = 10                     # the first line has about 2 seconds to stop the scroll, and fits the cloud


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
    if text.count("!") > 3:
        problems.append("more than three exclamation marks")
    if not any("*" in line for line in script["lines"]):
        problems.append("no *emphasis* marked")
    first = script["lines"][0].replace("*", "")
    if len(first.split()) > MAX_HOOK_WORDS:
        problems.append(f"hook (first line) longer than {MAX_HOOK_WORDS} words")
    if not script["lines"][-1].rstrip().endswith("?"):
        problems.append("last line is not a question for the viewer")
    if first.rstrip().endswith("?") and first.lower().startswith(("have you", "do you", "are you", "ever wonder")):
        problems.append("lazy question hook")
    # Every number in the script must appear in the fact (no invented stats, no citation years).
    fact_text = fact["claim"].lower()
    for num in re.findall(r"\d+(?:\.\d+)?", text):
        if num not in fact_text:
            problems.append(f"number '{num}' is not in the fact")
    # Straight facts: who ran the study goes in the comment, not the video.
    surname = fact["source"].split(",")[0].split("&")[0].split(" et al")[0].strip().lower()
    for word in (*STUDY_WORDS, surname):
        if re.search(r"\b" + re.escape(word), low):
            problems.append(f"mentions '{word}': state the finding itself, the source goes in the comment")
    return problems
