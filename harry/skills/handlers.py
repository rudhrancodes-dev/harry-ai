"""Deterministic handlers for skills that don't need the LLM."""
from __future__ import annotations

import ast
import operator
import platform
import random
import re
import subprocess
import time
from datetime import datetime

_SAFE_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow,
    ast.USub: operator.neg, ast.UAdd: operator.pos, ast.FloorDiv: operator.floordiv,
}


def _safe_eval(expr: str) -> float:
    tree = ast.parse(expr, mode="eval")

    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _SAFE_OPS:
            return _SAFE_OPS[type(node.op)](visit(node.operand))
        raise ValueError("unsafe expression")

    return visit(tree)


def _numbers(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text)]


def _osa(script: str) -> bool:
    try:
        subprocess.run(["osascript", "-e", script], check=True, timeout=4,
                       capture_output=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _mac_only() -> str | None:
    if platform.system() != "Darwin":
        return "That action is only supported on macOS, sir."
    return None


# ── arithmetic ────────────────────────────────────────────────────────────

def calculator(utterance: str) -> str:
    cleaned = utterance.lower()
    for k, v in {"plus": "+", "minus": "-", "times": "*", "multiplied by": "*",
                 "divided by": "/", "over": "/", "x": "*"}.items():
        cleaned = cleaned.replace(k, v)
    expr = re.search(r"[-+*/().\d\s]+", cleaned)
    if not expr:
        return "I could not parse a calculation, sir."
    try:
        value = _safe_eval(expr.group(0).strip())
    except Exception:
        return "I could not evaluate that expression, sir."
    return f"The answer is {value:g}, sir."


def percent(utterance: str) -> str:
    nums = _numbers(utterance)
    if len(nums) < 2:
        return "Please give me a percent and a number, sir."
    return f"That is {nums[0] * nums[1] / 100:g}, sir."


def tip(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me the bill amount, sir."
    bill = nums[0]
    rate = nums[1] if len(nums) > 1 else 15.0
    return f"On a bill of {bill:g}, a {rate:g} percent tip is {bill * rate / 100:.2f}, sir."


def age(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please tell me the birth year, sir."
    return f"That person would be about {datetime.now().year - int(nums[0])} years old, sir."


def distance(utterance: str) -> str:
    nums = _numbers(utterance)
    if len(nums) < 2:
        return "Please give me a speed and a duration, sir."
    return f"That comes to about {nums[0] * nums[1]:g} units of distance, sir."


# ── unit conversions ──────────────────────────────────────────────────────

def length(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me a length, sir."
    n = nums[0]
    if "feet" in utterance:
        return f"{n:g} feet is about {n * 0.3048:.2f} metres, sir."
    return f"{n:g} metres is about {n * 3.281:.2f} feet, sir."


def mass(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me a mass, sir."
    n = nums[0]
    if "pound" in utterance:
        return f"{n:g} pounds is about {n * 0.4536:.2f} kilograms, sir."
    return f"{n:g} grams is about {n / 28.35:.2f} ounces, sir."


def temperature(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me a temperature, sir."
    n = nums[0]
    if "fahrenheit to celsius" in utterance:
        return f"{n:g} fahrenheit is {(n - 32) * 5 / 9:.1f} celsius, sir."
    return f"{n:g} celsius is {n * 9 / 5 + 32:.1f} fahrenheit, sir."


def weight(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me a weight, sir."
    n = nums[0]
    if "pounds to kilograms" in utterance:
        return f"{n:g} pounds is about {n * 0.4536:.2f} kilograms, sir."
    return f"{n:g} kilograms is about {n / 0.4536:.2f} pounds, sir."


def roman(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me a number, sir."
    n = int(nums[0])
    if not 1 <= n <= 3999:
        return "Roman numerals only cover one through three thousand nine hundred ninety-nine, sir."
    pairs = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
             (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
             (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    out = ""
    for value, sym in pairs:
        while n >= value:
            out += sym
            n -= value
    return f"That is {out}, sir."


def binary(utterance: str) -> str:
    nums = _numbers(utterance)
    if not nums:
        return "Please give me a number, sir."
    return f"That is binary {bin(int(nums[0]))[2:]}, sir."


# ── mac system control ────────────────────────────────────────────────────

def close_app(utterance: str) -> str:
    if (msg := _mac_only()): return msg
    match = re.search(r"close (?:the )?app (\w+)|quit (?:the )?app (\w+)", utterance)
    name = (match.group(1) or match.group(2)) if match else None
    if not name:
        return "Which application should I close, sir?"
    return f"Closing {name.title()}, sir." if _osa(f'tell application "{name}" to quit') \
        else f"I could not close {name}, sir."


def volume_up(_u: str) -> str:
    if (msg := _mac_only()): return msg
    return "Volume up, sir." if _osa("set volume output volume (output volume of (get volume settings) + 12)") \
        else "I could not adjust volume, sir."


def volume_down(_u: str) -> str:
    if (msg := _mac_only()): return msg
    return "Volume down, sir." if _osa("set volume output volume (output volume of (get volume settings) - 12)") \
        else "I could not adjust volume, sir."


def brightness_up(_u: str) -> str:
    if (msg := _mac_only()): return msg
    _osa('tell application "System Events" to key code 144')
    return "Brightness up, sir."


def brightness_down(_u: str) -> str:
    if (msg := _mac_only()): return msg
    _osa('tell application "System Events" to key code 145')
    return "Brightness down, sir."


def screenshot(_u: str) -> str:
    if (msg := _mac_only()): return msg
    path = f"/tmp/harry-{int(time.time())}.png"
    try:
        subprocess.run(["screencapture", "-x", path], check=True, timeout=4)
    except Exception:
        return "I could not capture the screen, sir."
    return f"Screenshot saved to {path}, sir."


def lock_screen(_u: str) -> str:
    if (msg := _mac_only()): return msg
    _osa('tell application "System Events" to keystroke "q" using {control down, command down}')
    return "Locking the screen, sir."


def battery(_u: str) -> str:
    try:
        out = subprocess.check_output(["pmset", "-g", "batt"], timeout=4, text=True)
    except Exception:
        return "I could not read the battery, sir."
    m = re.search(r"(\d+)%", out)
    return f"Battery is at {m.group(1)} percent, sir." if m else "Battery status unavailable, sir."


# ── randomisers ───────────────────────────────────────────────────────────

def breathing(_u: str) -> str:
    return ("Inhale for four, hold for four, exhale for four, hold for four. "
            "Repeat that cycle three times, sir.")


def coin(_u: str) -> str:
    return f"{random.choice(('Heads', 'Tails'))}, sir."


def dice(utterance: str) -> str:
    sides = 6
    nums = _numbers(utterance)
    if nums:
        sides = max(2, min(100, int(nums[0])))
    return f"You rolled a {random.randint(1, sides)}, sir."


HANDLERS = {
    "calculator": calculator, "percent": percent, "tip": tip, "age": age,
    "distance": distance, "length": length, "mass": mass,
    "temperature": temperature, "weight": weight,
    "roman": roman, "binary": binary,
    "close_app": close_app, "volume_up": volume_up, "volume_down": volume_down,
    "brightness_up": brightness_up, "brightness_down": brightness_down,
    "screenshot": screenshot, "lock_screen": lock_screen, "battery": battery,
    "breathing": breathing, "coin": coin, "dice": dice,
}
