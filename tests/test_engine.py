from app.engine import classify, reply_for
from app.tools import convert_units, safe_eval


def test_safe_eval_order_of_operations():
    assert safe_eval("2 + 3 * 4") == 14
    assert safe_eval("2^10") == 1024
    assert safe_eval("(12 + 8) / 4") == 5


def test_convert_temperature_and_distance():
    assert round(convert_units(32, "F", "C"), 5) == 0
    assert round(convert_units(5, "km", "mi"), 2) == 3.11


def test_greeting_intent():
    assert classify("hello there")[0] == "greeting"
    result = reply_for("hi")
    assert "Lumen" in result.reply


def test_math_reply():
    result = reply_for("what is 12 * 8")
    assert result.intent == "math"
    assert "96" in result.reply


def test_notes_roundtrip():
    sid = "test-session"
    reply_for("remember this: ship the portfolio", session_id=sid)
    listed = reply_for("show notes", session_id=sid)
    assert "ship the portfolio" in listed.reply


def test_wellbeing_does_not_play_therapist():
    result = reply_for("I feel overwhelmed and anxious")
    assert "988" in result.reply
    assert result.intent == "wellbeing"


def test_unknown_is_honest():
    result = reply_for("write a 40-page novel about quantum shrimp")
    assert result.intent == "unknown"
    assert "LLM" in result.reply or "don’t improvise" in result.reply or "don't improvise" in result.reply
