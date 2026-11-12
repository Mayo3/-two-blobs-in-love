"""Writes a script for one fact with a free LLM, then holds it to the same bar as the
hand-written samples. A script that keeps failing the checks is never rendered.
"""
import json
import os
import re

from .captions import PALETTES
from .cartoon.director import ACTIONS, describe_actions
from .cartoon.scenes import Scene
from .llm import chat_json
from .produce import ROOT
from .style import BANNED_PHRASES, MAX_HOOK_WORDS, MAX_SENTENCE_WORDS, MAX_WORDS, MIN_WORDS, STUDY_WORDS, check_script

# actions that put nothing where the hook's cloud sits; line 1 gets "idle" if the writer picks another
HOOK_SAFE = {"idle", "wave", "turn_toward", "hold_hands", "hug", "calm", "date", "sniff", "texting", "far_apart",
             "twin", "unmatch", "old", "young", "alone", "stranger", "watched"}
STIFF = re.compile(r"\b(let us|I am|you are|we are|they are)\b(?= \w)", re.I)  # nobody says these out loud

FORMATS = {
    "reveal": "Pip wonders about something; Bo gives the finding straight, then the detail that makes it surprising.",
    "myth-vs-fact": "Pip states the popular belief, sure of himself; Bo overturns it with the finding.",
    "try-this": "Bo shares the finding and they turn it into one small thing to try together today; Pip wants to try it at once.",
    "quiz": "Bo quizzes Pip (which couples..., what happened when...); Pip guesses wrong, then Bo reveals.",
}

SYSTEM = f"""You write scripts for "Two Blobs in Love", a TikTok channel of science-backed facts about couples.
Each video is a short conversation between the channel's two cartoon blobs, a couple, who also act out every line:
- Pip (in the action list: A; pink, a sprout on his head): eager, sure of himself, guesses first and is often wrong,
  takes everything personally, turns every finding into a plan or a joke about the two of them.
- Bo (B; purple, a bow): knows the findings, dry and teasing, enjoys being right, fond of Pip all the same.
They sound like a real couple on the sofa: short lines, quick replies, a little teasing. They say each other's
name once or twice in a video, not in every line. Plain spoken English. Specific and concrete.
Never preachy, never salesy, never generic.

Every script has this shape:
1. the hook (see below),
2. Pip's guess or belief: confident, and wrong or only half right,
3. Bo does NOT answer yet. She teases him, or starts on the odd concrete thing people in the study actually did
   or that was measured (were tied wrist to wrist, sniffed T-shirts, held a hand while waiting for a shock).
   The viewer must still be wondering who is right,
4. the finding: it lands in the second half of the script, never in Bo's first reply. A reply like "It really can."
   straight after the hook kills the video: there is nothing left to wait for,
5. Pip's punchline: one line that could only follow this fact, a joke at his own cost or a plan for the two of them
   ("So I should point at more birds."), not a general remark,
6. the closing question to the viewer.
They talk the way people talk: always "let's", "I'm", "you're", "don't", "that's", never "let us", "I am", "you are".

Audience: mostly 18 to 34, dating or in their first serious relationships. Don't assume they are married:
say "married couples", "newlyweds", "husband" or "divorce" only when describing who was studied.
Light and curious beats heavy: playful questions about love get watched far longer than warnings about breakups.

Hard rules:
- Use ONLY the fact you are given. Every number you say must appear in the fact. No other statistics.
- Never invent details about the study (no made-up participant counts, places, or quotes).
- Bo only ever states what the fact says. Pip may guess or believe something wrong, but never with a number, and Bo sets it right.
- Tell what people in the study did and what was found, but never name researchers, scientists, universities or
  journals, and never say a year. The source goes in a comment.
  Keep it true: if only women, or only married couples, were studied, say so in a few words.
- {MIN_WORDS}-{MAX_WORDS} words in total, 7-10 lines, each line said by one of them. Most lines are short (2 to 10 words);
  the line with the finding may be longer. At most {MAX_SENTENCE_WORDS} words per sentence. Both speak at least three times.
- Line 1 is the hook, at most {MAX_HOOK_WORDS} words, with no names in it. It is shown on screen while it is spoken, alone, so it must work on its own and make someone stop scrolling.
  Open a question the video then answers, so viewers stay to find out: a yes-or-no question about something people
  believe or wonder about ("Do couples really start to *look alike*?", "Can eye contact make you *fall* for someone?"),
  or a belief stated as fact that the video will overturn. Never give the answer away in line 1.
  Not a lazy question like "Have you ever..." or "Do you...".
  The viewer must not be able to guess the answer. If the honest answer is an obvious yes, the hook is dead:
  "Does bad sleep ruin your arguments?" (of course it does) loses to "Is tomorrow's fight decided *tonight*?".
  Put the oddest concrete thing in the fact into the hook (a bird, a voodoo doll, a sweaty T-shirt).
- Write numbers as digits and spell out "percent" (e.g. "86 percent") so the narrator reads them right.
- When a line is about a word itself, put that word in double quotes, or it reads like a typo on screen:
  Can the word "the" predict your future? Couples who say "we" more.
- Mark 1-4 key words or numbers with *asterisks* (they get highlighted).
- The last line is said to the viewer, not to each other, with no names in it: a question the viewer can answer in a word or two (yes or no, this or that, A or B), so they reply in the comments. Never "follow for more" or "comment below".
  At most {MAX_HOOK_WORDS} words: it is shown whole on screen, like the hook. Best is one that splits people or makes them
  tell on themselves or their partner ("Who falls asleep first, you or them?"), not one everybody answers the same way.
- They react like people: "Wait, what?", "No way.", "Ha!", "Ohh.", "Hmm.", "Pfff." A reaction of one to three
  words is a fine line of its own, and a question may be a real, surprised question. At most three exclamation
  marks. No emojis. No hashtags in the script.
- Never use these words or phrases: {", ".join(BANNED_PHRASES)}.

Cartoon: for every line pick an action (or a list of 2-3 actions that split the line) from this list.
A is Pip and B is Bo. The one speaking moves their mouth by themselves. Pick actions that literally show what the line says. Use "name:arg" only where the description mentions an arg.
{describe_actions()}

Palettes (caption highlight colours): {", ".join(PALETTES)}.

Reply with JSON only:
{{"hooks": [{{"hook": "...", "a_stranger_would_guess": "...", "the_truth": "..."}}, ...], "title": "...", "scene": "...", "palette": "...", "speakers": ["pip" or "bo", ...], "sounds": [null or "chuckle" ..., ...], "lines": ["..."], "beats": ["action" or ["action", "action"], ...], "caption": "..."}}
- "hooks": write these first: three different candidates for line 1, each from another angle. For each, write the
  answer a stranger would guess in one second, and the truth. Line 1 must be a hook whose guess is wrong, or that
  nobody can guess. If the stranger's guess is simply right ("yes, of course"), throw that hook away.
- The action for line 1 must leave the space above their heads free for the hook: one of {", ".join(sorted(HOOK_SAFE))}.
- "title": under 40 characters, a punchy name for the video (used in notifications and the history).
- "speakers", "sounds" and "beats" have exactly one entry per line.
- "sounds": a sound the speaker makes just before a line, or null: "chuckle" (teasing, amused), "laugh" (it really is
  funny), "gasp" (surprised, or a sudden idea), "sigh" (fond or fed up), "groan" (caught being wrong). Two or three in
  a video, where a person really would make one: Bo chuckling before she teases, Pip gasping at the finding or
  groaning when he's wrong, a laugh after the punchline. Never on line 1, never on two lines in a row.
- "caption": one short natural sentence (under 120 characters), no hashtags. TikTok search reads it, so name the
  subject in the plain words someone would type ("why couples start to look alike", "holding hands and stress",
  "who says I love you first"), in the first half of the sentence. Say what the video is about without giving the
  answer away. No empty teasers: never "find out", "more than you think", "might surprise you", "you need to know".
  In the TikTok caption it comes right after your closing question, so don't repeat the question.
"""


def examples():
    samples = json.load(open(os.path.join(ROOT, "samples", "scripts.json"), encoding="utf-8"))
    keep = ("title", "scene", "palette", "speakers", "sounds", "lines", "beats")
    return "\n\n".join(
        f"Example ({s['format']}):\n" + json.dumps({k: s[k] for k in keep}, ensure_ascii=False) for s in samples
    )


def validate(script, fact, scenes=Scene.kinds):
    problems = check_script(script, fact)
    lines, beats = script.get("lines", []), script.get("beats", [])
    if not 7 <= len(lines) <= 10:
        problems.append(f"{len(lines)} lines (want 7-10)")
    speakers = script.get("speakers", [])
    if len(speakers) != len(lines) or any(s not in ("pip", "bo") for s in speakers):
        problems.append('"speakers" needs one of "pip" or "bo" for every line')
    elif min(speakers.count("pip"), speakers.count("bo")) < 3:
        problems.append("Pip and Bo must each speak at least three times")
    for i in (0, -1):
        if lines and re.search(r"\b(pip|bo)\b", lines[i].lower()):
            problems.append(f"line {'1' if i == 0 else 'last'} must not contain their names")
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
    if lines and len(lines[-1].replace("*", "").split()) > MAX_HOOK_WORDS:
        problems.append(f"last line longer than {MAX_HOOK_WORDS} words")
    caption = script.get("caption", "").lower()
    problems += [f"caption has banned phrase: '{p}'" for p in BANNED_PHRASES if p in caption]
    problems += [f"caption has an empty teaser ('{p}'): say what the video is about in searchable words"
                 for p in ("find out", "more than you think", "surprise you", "need to know") if p in caption]
    for line in lines:
        m = re.search(r"\bthe word (?![\"“'‘]|\*[\"“'‘])\*?(\w+)", line, re.I)
        if m:
            problems.append(f'put the word in double quotes: the word "{m.group(1)}"')
    for line in lines:
        m = STIFF.search(line.replace("*", ""))
        if m:
            problems.append(f"'{m.group(1)}' sounds stiff: use the contraction, as people do when they talk")
    if not script.get("title") or len(script["title"]) > 45:
        problems.append("title missing or too long")
    if "#" in script.get("caption", ""):
        problems.append("caption contains hashtags")
    if any(w in script.get("caption", "").lower() for w in STUDY_WORDS):
        problems.append("caption mentions who did the study; keep it a straight fact")
    return problems


def write_script(fact, fmt, scenes=Scene.kinds, tries=3):
    """Return a validated script dict, or raise after `tries` failed attempts."""
    user = (
        f"Fact: {fact['claim']}\n\n"
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
        script["title"] = str(script.get("title", "")).replace("*", "")
        beats = script.get("beats") or [None]
        first = beats[0][0] if isinstance(beats[0], list) and beats[0] else beats[0]
        if isinstance(first, str) and first.partition(":")[0] not in HOOK_SAFE:
            beats[0] = "idle"  # e.g. a thought bubble would sit half hidden under the hook
        script["fact"], script["format"] = fact["id"], fmt
        problems = validate(script, fact, scenes)
        if not problems:
            return script
        print(f"attempt {attempt + 1} rejected: {problems}")
    raise RuntimeError(f"no acceptable script after {tries} tries: {problems}")
