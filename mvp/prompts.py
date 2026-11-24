"""Build a transparent, user-editable prompt for SceneSound's audio generator."""


def build_prompt(
    scene: str, mood: str, audio_type: str, duration: int, examples: list[dict]
) -> str:
    """Combine the scene, mood, duration, and user-selected retrieval references.

    This function only drafts text; it does not call a model or generate audio.
    The Streamlit editor should let the user review and revise the result before
    passing that final text to the generation layer.
    """
    scene_text = str(scene or "").strip()
    mood_text = str(mood or "").strip()
    if not scene_text:
        raise ValueError("Please enter a scene description.")
    if duration < 1:
        raise ValueError("Duration must be positive.")

    formats = {
        "Ambience": (
            "Create a cohesive environmental soundscape. Do not add music or "
            "intelligible speech unless the scene explicitly calls for it."
        ),
        "Sound effect": (
            "Create a focused sound effect (SFX) that fits the described scene. "
            "Do not add music or intelligible speech unless explicitly requested."
        ),
        "Instrumental music": (
            "Create instrumental music with no intelligible vocals, shaped to "
            "fit the described scene."
        ),
    }
    if audio_type not in formats:
        raise ValueError("Choose Ambience, Sound effect, or Instrumental music.")

    lines = [
        formats[audio_type],
        f"Scene: {scene_text}",
    ]
    if mood_text:
        lines.append(f"Intended mood: {mood_text}.")
    lines.append(f"Target duration: {duration} seconds.")

    descriptions = [
        str(row.get("description", "")).strip()
        for row in (examples or [])
        if str(row.get("description", "")).strip()
    ]
    if descriptions:
        lines.extend(
            [
                "Use these user-selected sound references as inspiration for "
                "texture, ambience, and sound character; do not reproduce them "
                "literally unless they fit the scene:",
                *[f"- {description}" for description in descriptions],
            ]
        )

    lines.append(
        "Keep the result coherent and appropriate to the scene. Preserve the "
        "user's stated details and exclusions."
    )
    # Duration must ALSO be supplied as a separate API parameter at generation.
    return "\n".join(lines)
