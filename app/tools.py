from __future__ import annotations

import ast
import operator
import re
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.FloorDiv: operator.floordiv,
}


def safe_eval(expr: str) -> float:
    """Evaluate a basic arithmetic expression without executing arbitrary code."""
    cleaned = expr.replace("^", "**")
    tree = ast.parse(cleaned, mode="eval")
    return _eval_node(tree.body)


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return float(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval_node(node.operand))
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    raise ValueError("Unsupported expression")


UNIT_TO_METERS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "inch": 0.0254,
    "ft": 0.3048,
    "feet": 0.3048,
    "yd": 0.9144,
    "mi": 1609.344,
}

UNIT_TO_GRAMS = {
    "mg": 0.001,
    "g": 1.0,
    "kg": 1000.0,
    "lb": 453.59237,
    "oz": 28.349523125,
}

TEMP_UNITS = {"c", "f", "k", "celsius", "fahrenheit", "kelvin"}


def convert_units(value: float, src: str, dest: str) -> float:
    s, d = src.lower(), dest.lower()
    if s in TEMP_UNITS and d in TEMP_UNITS:
        c = _to_celsius(value, s)
        return _from_celsius(c, d)
    if s in UNIT_TO_METERS and d in UNIT_TO_METERS:
        return value * UNIT_TO_METERS[s] / UNIT_TO_METERS[d]
    if s in UNIT_TO_GRAMS and d in UNIT_TO_GRAMS:
        return value * UNIT_TO_GRAMS[s] / UNIT_TO_GRAMS[d]
    raise ValueError(f"Cannot convert {src} to {dest}")


def _to_celsius(value: float, unit: str) -> float:
    if unit in {"c", "celsius"}:
        return value
    if unit in {"f", "fahrenheit"}:
        return (value - 32) * 5 / 9
    if unit in {"k", "kelvin"}:
        return value - 273.15
    raise ValueError("Unknown temperature unit")


def _from_celsius(value: float, unit: str) -> float:
    if unit in {"c", "celsius"}:
        return value
    if unit in {"f", "fahrenheit"}:
        return value * 9 / 5 + 32
    if unit in {"k", "kelvin"}:
        return value + 273.15
    raise ValueError("Unknown temperature unit")


def now_text(tz_name: str | None = None) -> str:
    tz = ZoneInfo(tz_name) if tz_name else timezone.utc
    stamp = datetime.now(tz)
    label = tz_name or "UTC"
    return stamp.strftime(f"%A, %B %d, %Y · %H:%M ({label})")


MATH_RE = re.compile(
    r"(?:what(?:'s| is)|calculate|compute|eval)?\s*([0-9.+\-*/^()%\s]+)\s*\??$",
    re.I,
)
CONVERT_RE = re.compile(
    r"(?:convert\s+)?(-?\d+(?:\.\d+)?)\s*([a-z°]+)\s+(?:to|in)\s+([a-z°]+)",
    re.I,
)
