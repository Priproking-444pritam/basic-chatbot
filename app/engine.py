from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field

from app.tools import CONVERT_RE, convert_units, now_text, safe_eval

_NOTES: dict[str, list[str]] = {}


@dataclass
class EngineResult:
    reply: str
    intent: str
    suggestions: list[str] = field(default_factory=list)
    source: str = "engine"


INTENTS: list[tuple[str, list[re.Pattern[str]], int]] = [
    ("greeting", [re.compile(r"\b(hi|hello|hey|yo|good (morning|afternoon|evening))\b", re.I)], 10),
    ("farewell", [re.compile(r"\b(bye|goodbye|see you|later|exit|quit)\b", re.I)], 10),
    ("thanks", [re.compile(r"\b(thanks|thank you|appreciate|thx)\b", re.I)], 8),
    ("identity", [re.compile(r"\b(who are you|your name|what are you|about you)\b", re.I)], 12),
    ("help", [re.compile(r"\b(help|what can you do|capabilities|commands|features)\b", re.I)], 12),
    ("time", [re.compile(r"\b(time|date|today|day is it|clock)\b", re.I)], 9),
    ("math", [re.compile(r"[\d]+\s*[\+\-\*/^%]\s*[\d]+|calculate|compute|what(?:'s| is)\s+\d", re.I)], 11),
    ("convert", [re.compile(r"\bconvert\b|\d+\s*(km|mi|kg|lb|c|f|celsius|fahrenheit)\b", re.I)], 11),
    ("interview", [re.compile(r"\b(interview|resume|star method|behavioral|hiring)\b", re.I)], 10),
    ("study", [re.compile(r"\b(study|learn|focus|pomodoro|revise|exam)\b", re.I)], 9),
    ("wellbeing", [re.compile(r"\b(anxious|stressed|overwhelmed|sad|lonely|burnout)\b", re.I)], 12),
    ("privacy", [re.compile(r"\b(privacy|data|store|remember me|tracking)\b", re.I)], 9),
    ("joke", [re.compile(r"\b(joke|funny|make me laugh)\b", re.I)], 8),
    ("note_add", [re.compile(r"\b(remember|note|save this|add to notes)\b", re.I)], 10),
    ("note_list", [re.compile(r"\b(notes|what did i save|show notes)\b", re.I)], 9),
    ("how_built", [re.compile(r"\b(how (are you|were you) (built|made)|architecture|tech stack)\b", re.I)], 11),
]


HELP_SUGGESTIONS = [
    "What can you do?",
    "Convert 72 F to C",
    "Interview tip for behavioral questions",
    "What time is it?",
]


def reply_for(message: str, session_id: str | None = None, history: list[dict] | None = None) -> EngineResult:
    sid = session_id or str(uuid.uuid4())
    text = message.strip()
    if not text:
        return EngineResult("Say something and I’ll meet you there.", "empty", HELP_SUGGESTIONS[:3], "engine")

    intent, _score = classify(text)
    notes = _NOTES.setdefault(sid, [])
    history = history or []

    handlers = {
        "greeting": _greeting,
        "farewell": _farewell,
        "thanks": _thanks,
        "identity": _identity,
        "help": _help,
        "time": _time,
        "math": _math,
        "convert": _convert,
        "interview": _interview,
        "study": _study,
        "wellbeing": _wellbeing,
        "privacy": _privacy,
        "joke": _joke,
        "note_add": lambda t: _note_add(t, notes),
        "note_list": lambda t: _note_list(notes),
        "how_built": _how_built,
    }
    handler = handlers.get(intent, _fallback)
    result = handler(text)
    result.intent = intent if intent in handlers else result.intent
    return result


def classify(text: str) -> tuple[str, int]:
    best, best_score = "unknown", 0
    for name, patterns, weight in INTENTS:
        if any(p.search(text) for p in patterns):
            if weight > best_score:
                best, best_score = name, weight
    return best, best_score


def _greeting(_text: str) -> EngineResult:
    return EngineResult(
        "Hey — I’m Lumen. I can help with math, conversions, study focus, interview prep, "
        "and quick notes. What’s on your mind?",
        "greeting",
        ["What can you do?", "Give me an interview tip", "12 * 17.5"],
    )


def _farewell(_text: str) -> EngineResult:
    return EngineResult("Take care. I’ll be here when you need a second brain.", "farewell", ["Start a new topic"])


def _thanks(_text: str) -> EngineResult:
    return EngineResult("Anytime. Want to keep going?", "thanks", ["Show my notes", "Another interview tip"])


def _identity(_text: str) -> EngineResult:
    return EngineResult(
        "I’m Lumen, a conversational assistant designed to run in the browser or on a small FastAPI backend. "
        "I start on-device so you can ship a real demo without an API key. Plug in an OpenAI-compatible model "
        "when you want open-ended generation.",
        "identity",
        ["How were you built?", "What about privacy?"],
    )


def _help(_text: str) -> EngineResult:
    return EngineResult(
        "Here’s what I’m good at right now:\n"
        "• Math and unit conversions\n"
        "• Time and date\n"
        "• Session notes (remember this…)\n"
        "• Interview and study coaching\n"
        "• Honest answers about privacy and how I’m built\n\n"
        "Try a chip below, or just type.",
        "help",
        HELP_SUGGESTIONS,
    )


def _time(_text: str) -> EngineResult:
    tz = None
    lowered = _text.lower()
    for name in ("UTC", "America/New_York", "America/Los_Angeles", "Europe/London", "Asia/Kolkata", "Asia/Tokyo"):
        if name.split("/")[-1].replace("_", " ").lower() in lowered or name.lower() in lowered:
            tz = name
            break
    if "ist" in lowered or "india" in lowered:
        tz = "Asia/Kolkata"
    return EngineResult(f"It’s {now_text(tz)}.", "time", ["What can you do?"])


def _math(text: str) -> EngineResult:
    expr = re.sub(r"[^0-9.+\-*/^()%\s]", " ", text)
    expr = " ".join(expr.split())
    try:
        value = safe_eval(expr)
        pretty = str(int(value)) if float(value).is_integer() else f"{value:.6g}"
        return EngineResult(f"{expr} = **{pretty}**", "math", ["Convert 5 km to mi", "What time is it?"])
    except Exception:
        return EngineResult(
            "I can evaluate expressions like `12 * (4 + 3)` or `2^10`. Try one of those.",
            "math",
            ["2^10", "15% of 240"],
        )


def _convert(text: str) -> EngineResult:
    match = CONVERT_RE.search(text.replace("°", ""))
    if not match:
        return EngineResult("Try: convert 72 F to C, or 5 km to mi.", "convert", ["72 F to C", "5 km to mi"])
    value, src, dest = float(match.group(1)), match.group(2), match.group(3)
    src = src.replace("°", "")
    dest = dest.replace("°", "")
    try:
        out = convert_units(value, src, dest)
        pretty = f"{out:.4g}"
        return EngineResult(f"{value:g} {src} → **{pretty} {dest}**", "convert", ["100 km to mi", "0 C to F"])
    except ValueError as exc:
        return EngineResult(str(exc), "convert", ["72 F to C"])


def _interview(_text: str) -> EngineResult:
    return EngineResult(
        "For behavioral interviews, use STAR and keep it tight:\n"
        "1. **Situation** — one sentence of context\n"
        "2. **Task** — what you owned\n"
        "3. **Action** — what *you* did (tools, tradeoffs, collaboration)\n"
        "4. **Result** — a number if you have one\n\n"
        "Practice prompt: “Tell me about a time you shipped under ambiguity.” "
        "Answer in under 90 seconds, then I can tighten it if you paste a draft.",
        "interview",
        ["How were you built?", "Study focus tip"],
    )


def _study(_text: str) -> EngineResult:
    return EngineResult(
        "Use a 50/10 focus block: 50 minutes on one outcome, 10 minutes away from the screen. "
        "Write the outcome as a verb (“finish the API tests”), not a vibe (“work on backend”). "
        "After two blocks, teach the idea out loud in 60 seconds — that’s the fastest memory check.",
        "study",
        ["Interview tip", "Remember this: finish API tests"],
    )


def _wellbeing(_text: str) -> EngineResult:
    return EngineResult(
        "That’s heavy, and you don’t have to carry it alone. I’m a software assistant, not a clinician. "
        "If you’re in crisis, contact local emergency services or a trusted person nearby. "
        "In the US, you can call or text **988**. If you want a small next step: drink water, "
        "stand up for one minute, and name one task that’s actually 10 minutes long.",
        "wellbeing",
        ["Study focus tip", "What can you do?"],
    )


def _privacy(_text: str) -> EngineResult:
    return EngineResult(
        "Default mode is on-device: messages stay in this browser tab unless you deploy the API. "
        "The optional FastAPI server keeps notes only in memory per session — no database, no ads, no training pipeline. "
        "If you connect an LLM key, those turns leave your machine to that provider. You’re in control of that switch.",
        "privacy",
        ["How were you built?", "What can you do?"],
    )


def _joke(_text: str) -> EngineResult:
    return EngineResult(
        "Why did the frontend refuse to argue with the API? It didn’t want a cross-origin relationship.",
        "joke",
        ["Another joke", "Interview tip"],
    )


def _note_add(text: str, notes: list[str]) -> EngineResult:
    payload = re.sub(
        r"^(please\s+)?(remember|note|save this|add to notes)\s*(that\s+|this\s*:?\s*)?",
        "",
        text,
        flags=re.I,
    ).strip(" .")
    if not payload:
        return EngineResult("Tell me what to remember. Example: remember this: ship the README.", "note_add", [])
    notes.append(payload)
    return EngineResult(f"Saved ({len(notes)}): {payload}", "note_add", ["Show my notes"])


def _note_list(notes: list[str]) -> EngineResult:
    if not notes:
        return EngineResult("No notes in this session yet. Say “remember this: …” to add one.", "note_list", [])
    body = "\n".join(f"{i}. {n}" for i, n in enumerate(notes, 1))
    return EngineResult(f"Session notes:\n{body}", "note_list", ["Remember this: follow up with recruiter"])


def _how_built(_text: str) -> EngineResult:
    return EngineResult(
        "Lumen is a hybrid assistant:\n"
        "• A scored intent engine (regex + tools) for reliable, testable answers\n"
        "• Safe math and unit conversion — no `eval()` of user code\n"
        "• A FastAPI layer for health checks, CORS, and optional LLM completion\n"
        "• A static site that runs the same engine in JavaScript so GitHub Pages works with zero servers\n\n"
        "That’s the interview-friendly part: it works offline, it’s tested, and the LLM is an adapter — not a requirement.",
        "how_built",
        ["What about privacy?", "What can you do?"],
    )


def _fallback(text: str) -> EngineResult:
    preview = text if len(text) < 80 else text[:77] + "…"
    return EngineResult(
        f"I heard “{preview}.” I don’t improvise long answers unless an LLM key is connected. "
        "I *can* help with math, conversions, notes, interview prep, and how this project is built.",
        "unknown",
        HELP_SUGGESTIONS,
    )
