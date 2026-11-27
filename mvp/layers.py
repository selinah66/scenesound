"""Offline audition sounds and editable directions for the Layers prototype."""
import io
import wave
import re

import numpy as np

QUALITIES = {
    "Ambience": ["Sparse, soft and distant", "Steady and textured", "Dense, close and turbulent"],
    "Action & Foley": ["Slow, light and distant", "Measured, clear and close", "Quick, sharp and insistent"],
    "Music": ["Spacious, sustained notes", "A measured rhythmic pulse", "Tightly spaced, urgent pulses"],
}


def suggest(scene):
    rules = [
        ("Tense", "tension|uneasy|abandoned|dark|alley|suspense"),
        ("Urgent", "chase|rush|urgent|running"),
        ("Joyful", "celebration|laughing|festival"),
        ("Calm", "quiet|still|gentle|peaceful"),
    ]
    for mood, pattern in rules:
        match = re.search(r"\b(" + pattern + r")\b", scene, re.I)
        if match:
            return mood, f'The description mentions “{match.group()}”.'
    return "Neutral", "No strong mood cue matched the description."


def direction(scene, mood, category, name, notes, intensity):
    return (f"Create an isolated {category.lower()} track: {name}. {notes}\n"
            f"Performance: {QUALITIES[category][intensity]}. Intended mood: {mood}.\n"
            f"Scene context: {scene}\nRender only the requested layer; exclude unrelated sounds.")


def demo(category, intensity, duration, seed):
    rate = 16000
    rng = np.random.default_rng(seed)
    t = np.arange(rate * duration) / rate
    noise = rng.normal(0, 1, len(t))
    if category == "Ambience":
        signal = np.convolve(noise, np.ones(6) / 6, mode="same") * (0.15 + intensity * 0.04)
        signal *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.37 * t)
    elif category == "Action & Foley":
        beat = t % [1.15, 0.72, 0.39][intensity]
        signal = np.exp(-beat * 24) * (0.38 * np.sin(2*np.pi*83*beat) + 0.12*noise)
    else:
        beat = t % [2, 1, 0.5][intensity]
        signal = 0.16 * np.exp(-beat*2) * (np.sin(2*np.pi*220*t) + 0.4*np.sin(2*np.pi*330*t))
    signal *= np.minimum(1, t*80) * np.minimum(1, (duration-t)*80)
    out = io.BytesIO()
    with wave.open(out, "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        wav.writeframes((np.clip(signal, -1, 1)*32767).astype("<i2").tobytes())
    return out.getvalue()
