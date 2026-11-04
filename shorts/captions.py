"""Builds an .ass subtitle file: word-by-word captions plus the fixed brand layout
(series label at the top, source citation at the bottom).
"""
import re

W, H = 1080, 1920
# TikTok safe zone: its caption text covers the bottom ~420px, buttons the right ~130px,
# the For You tabs the top ~250px. One caption line sits just above the bottom overlay.
CAPTION_Y = 1440
HEADLINE_Y = 540
HOOK_SECONDS = 2.8  # how long the big hook title stays up
HOOK_Y = 570  # centre of the hook title (and the cloud behind it)
MAX_WORDS_PER_CHUNK = 3
MAX_CHARS_PER_CHUNK = 15  # keeps the line clear of TikTok's buttons on the right

PALETTES = {
    # gradient colours (hex RGB), caption accent, emphasis colour
    "plum": {"bg": ["2a0f2e", "6b1f4a", "b8475e"], "accent": "FFB4A2", "emph": "FFD166"},
    "night": {"bg": ["0d1b2a", "1b3a5c", "3e6e8e"], "accent": "9AD1FF", "emph": "FFD166"},
    "sunset": {"bg": ["3b1424", "a33d3d", "e8875a"], "accent": "FFE3B3", "emph": "FFF1A8"},
}


def ass_color(rgb_hex, alpha="00"):
    r, g, b = rgb_hex[0:2], rgb_hex[2:4], rgb_hex[4:6]
    return f"&H{alpha}{b}{g}{r}".upper()


def tokenize(lines):
    """Split script lines into display tokens, tracking *emphasis* spans."""
    tokens = []
    emph = False
    for li, line in enumerate(lines):
        for raw in line.split():
            starts = raw.startswith("*") or (raw[:1] in "\"'(" and raw[1:2] == "*")
            if starts:
                emph = True
            text = raw.replace("*", "")
            tokens.append({"text": text, "emph": emph, "line": li})
            if raw.rstrip(".,!?;:\"')…").endswith("*"):
                emph = False
    return tokens


def line_times(tokens, n_lines, duration):
    """(start, end) of each script line, from aligned tokens."""
    starts = [None] * n_lines
    for t in tokens:
        if starts[t["line"]] is None:
            starts[t["line"]] = t["start"]
    starts[0] = 0.0
    for i in range(1, n_lines):
        if starts[i] is None:
            starts[i] = starts[i - 1]
    return [(starts[i], starts[i + 1] if i + 1 < n_lines else duration) for i in range(n_lines)]


def _norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())


def align(tokens, words):
    """Give each display token a start/end from the TTS word timings."""
    wi = 0
    for t in tokens:
        target = _norm(t["text"])
        if not target:
            continue
        acc = ""
        start = end = None
        while wi < len(words) and len(acc) < len(target):
            wn = _norm(words[wi]["text"])
            if not wn:
                wi += 1
                continue
            if start is None:
                start = words[wi]["start"]
            acc += wn
            end = words[wi]["end"]
            wi += 1
        t["start"], t["end"] = start, end
    # Fill gaps (punctuation-only tokens or alignment misses) from neighbours.
    last = 0.0
    for t in tokens:
        if t.get("start") is None:
            t["start"] = t["end"] = last
        last = t["end"]
    return tokens


def chunk(tokens):
    """Group tokens into short caption chunks, breaking at punctuation and pauses."""
    chunks, cur = [], []
    for i, t in enumerate(tokens):
        cur.append(t)
        nxt = tokens[i + 1] if i + 1 < len(tokens) else None
        chars = sum(len(x["text"]) + 1 for x in cur)
        brk = (
            nxt is None
            or len(cur) >= MAX_WORDS_PER_CHUNK
            or chars + len(nxt["text"]) > MAX_CHARS_PER_CHUNK
            or t["text"][-1] in ".,!?:;…"
            or nxt["start"] - t["end"] > 0.35
        )
        if brk:
            chunks.append(cur)
            cur = []
    return chunks


def ts(sec):
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int(sec % 3600 // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def wrap(text, width):
    """Manual line breaks (\\N) so big headlines wrap evenly."""
    target = len(text) / max(1, -(-len(text) // width))  # even line lengths, no orphans
    lines, cur = [], ""
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > target + 2:
            lines.append(cur)
            cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur:
        lines.append(cur)
    return "\\N".join(lines)


def esc(text):
    return text.replace("\\", "\\\\").replace("{", "(").replace("}", ")")


def headlines(tokens, title, duration):
    """Big serif text above the captions: the title first, then each *emphasis* phrase,
    each held until the next one appears (at most ~6s)."""
    spans, cur = [], None
    for t in tokens:
        if t["emph"]:
            if cur is None:
                cur = {"start": t["start"], "words": []}
            cur["words"].append(t["text"])
        elif cur is not None:
            spans.append(cur)
            cur = None
    if cur is not None:
        spans.append(cur)
    items = []
    first = spans[0]["start"] if spans else duration
    items.append({"start": 0.0, "end": max(2.5, min(first, 4.5)), "text": title, "title": True})
    for s in spans:
        text = " ".join(s["words"]).strip(" .,!?;:\"'…")
        text = re.sub(r"(\d+) percent", r"\1%", text)
        items.append({"start": max(s["start"], items[-1]["end"] if items[-1].get("title") else 0), "text": text, "title": False})
    for i, it in enumerate(items):
        nxt = items[i + 1]["start"] if i + 1 < len(items) else duration
        if "end" not in it or it["end"] > nxt:
            it["end"] = min(nxt, it["start"] + 6.0) if not it.get("title") else nxt
    return [it for it in items if it["end"] - it["start"] > 0.3]


def build_ass(tokens, duration, palette, source, series_label, title="", big_text=False, hook=False):
    """big_text: title, then every *emphasis* phrase in big letters. hook: only the title,
    big, for the first seconds (most people start watching muted)."""
    pal = PALETTES[palette]
    white = ass_color("FFFFFF")
    accent = ass_color(pal["accent"])
    emph = ass_color(pal["emph"])
    shadow = ass_color("140810", "60")
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Caption,Archivo Black,80,{white},{white},{ass_color('3b2340')},{shadow},0,0,0,0,100,100,0,0,1,7,5,5,90,90,0,1
Style: Label,DM Serif Display,54,{white},{white},{ass_color('3b2340')},{shadow},0,1,0,0,100,100,1,0,1,4,3,8,80,80,300,1
Style: Headline,DM Serif Display,150,{emph},{white},{ass_color('3b2340')},{shadow},0,0,0,0,100,100,0,0,1,7,6,5,90,90,0,1
Style: Title,DM Serif Display,104,{white},{white},{ass_color('3b2340')},{shadow},0,0,0,0,100,100,0,0,1,6,6,5,90,90,0,1
Style: Hook,Fredoka SemiBold,76,{ass_color('3b2340')},{ass_color('3b2340')},{white},{ass_color('000000', 'FF')},0,0,0,0,100,100,0,0,1,0,0,5,90,90,0,1
Style: Source,DM Serif Display,34,{white},{white},{ass_color('3b2340')},{shadow},0,1,0,0,100,100,0,0,1,4,2,8,90,90,370,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    ev.append(f"Dialogue: 1,{ts(0)},{ts(duration)},Label,,0,0,0,,{{\\fad(400,0)}}{esc(series_label)}")
    heads = headlines(tokens, title, duration) if big_text else []
    if hook and title:
        # dark text inside a white cloud (drawn by the cartoon), readable on every scene and palette
        heads = [{"start": 0.0, "end": min(HOOK_SECONDS, duration), "text": title, "title": True, "style": "Hook"}]
    source_at = HOOK_SECONDS if hook else 1.0  # don't clutter the hook
    ev.append(f"Dialogue: 1,{ts(source_at)},{ts(duration)},Source,,0,0,0,,{{\\fad(600,0)}}Source: {esc(source)}")

    for it in heads:
        style = it.get("style") or ("Title" if it["title"] else "Headline")
        anim = "\\fad(250,200)\\fscx92\\fscy92\\t(0,220,\\fscx100\\fscy100)"
        y = HOOK_Y if style == "Hook" else HEADLINE_Y
        ev.append(f"Dialogue: 2,{ts(it['start'])},{ts(it['end'])},{style},,0,0,0,,{{\\pos({W // 2},{y})\\q2{anim}}}{wrap(esc(it['text']), 14 if it['title'] else 12)}")

    chunks = chunk(tokens)
    for ci, ch in enumerate(chunks):
        chunk_end = chunks[ci + 1][0]["start"] if ci + 1 < len(chunks) else duration
        for wi, t in enumerate(ch):
            start = t["start"]
            end = ch[wi + 1]["start"] if wi + 1 < len(ch) else chunk_end
            if end <= start:
                continue
            parts = []
            for wj, u in enumerate(ch):
                col = emph if u["emph"] else white
                if wj == wi:
                    col = emph if u["emph"] else accent
                    parts.append(f"{{\\c{col}\\fscx108\\fscy108}}{esc(u['text'])}{{\\fscx100\\fscy100}}")
                else:
                    parts.append(f"{{\\c{col}}}{esc(u['text'])}")
            # Pop in when a new chunk appears.
            pop = "{\\fscx88\\fscy88\\t(0,90,\\fscx100\\fscy100)}" if wi == 0 else ""
            size = ""
            ev.append(f"Dialogue: 0,{ts(start)},{ts(end)},Caption,,0,0,0,,{{\\pos({W // 2},{CAPTION_Y})}}{pop}{size}{' '.join(parts)}")
    return head + "\n".join(ev) + "\n"
