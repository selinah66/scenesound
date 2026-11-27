"""Infer emotional tone and energy by proximity to labeled scene examples."""
from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer

# Each reference has an emotional tone and an energy, both from -100 to +100.
EXAMPLES = [
    ("rainy alley lone figure stops at a door uneasy suspense waiting in shadows", -65, -32),
    ("empty apartment lonely grief mourning sad silent aftermath", -75, -68),
    ("quiet dark forest eerie stillness fear creeping dread", -68, -47),
    ("chase running danger alarms panic frantic urgent terrified escape", -86, 91),
    ("angry crowd shouting tense confrontation loud thunder storm", -69, 73),
    ("battle traffic crashing violent chaos sirens speeding cars", -81, 83),
    ("peaceful calm lake gentle breeze tranquil relaxing slow sunrise birdsong", 78, -72),
    ("warm kitchen soft light comfortable home safe tender reunion", 74, -52),
    ("hopeful quiet beach waves soft rain garden resting content", 62, -61),
    ("joyful vibrant celebration festival dancing laughing cheering fireworks", 89, 83),
    ("playful excited friends racing energetic bright upbeat adventure", 71, 68),
    ("triumphant stadium victory lively concert applause celebration", 85, 90),
]


@lru_cache(maxsize=1)
def reference_index():
    model = TfidfVectorizer(stop_words="english", sublinear_tf=True)
    return model, model.fit_transform(row[0] for row in EXAMPLES)


def suggest_point(scene):
    model, references = reference_index()
    scores = (references @ model.transform([scene]).T).toarray().ravel()
    best = scores.max()
    if best == 0:
        return [0, 0]
    matches = [(score**2, row) for score, row in zip(scores, EXAMPLES) if score >= best * 0.5]
    return [round(sum(w * row[i] for w, row in matches) / sum(w for w, _ in matches))
            for i in (1, 2)]


def mood_direction(tone, energy):
    label = "Neutral" if tone == energy == 0 else (
        ("Tense" if tone < 0 else "Exhilarating") if energy > 0 else
        ("Uneasy" if tone < 0 else "Peaceful"))
    return (f"{label}. Emotional tone {tone:+d} (−100 dark to +100 bright); "
            f"energy {energy:+d} (−100 still to +100 driven)")
