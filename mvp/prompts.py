"""A transparent prompt template for the team to inspect and improve."""


def build_prompt(
    scene: str, mood: str, audio_type: str, duration: int, examples: list[dict]
) -> str:
    if not scene.strip():
        raise ValueError("Please enter a scene description.")
    if duration < 1:
        raise ValueError("Duration must be positive.")

    formats = {
        "Ambience": "Environmental background ambience.",
        "Sound effect": "TrackType: SFX.",
        "Instrumental music": "Instrumental music, no intelligible vocals.",
    }
    lines = [
        formats[audio_type],
        f"Scene description: {scene.strip()}",
        f"Desired mood: {mood}.",
        f"Requested duration: {duration} seconds.",
    ]
    if examples:
        lines.append("Sound references selected by the user:")
        lines.extend(f"- {row['description']}" for row in examples)
    # Duration must ALSO be supplied as an API parameter when that is implemented.
    return "\n".join(lines)
