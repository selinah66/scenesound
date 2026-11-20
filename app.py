"""Run from this folder with: python -m streamlit run app.py"""

from pathlib import Path

import streamlit as st

from scenesound.nlp import load_sound_descriptions, retrieve_examples
from scenesound.prompts import build_prompt

st.set_page_config(page_title="SceneSound starter", page_icon="🎬", layout="centered")
st.title("SceneSound")
st.caption("Local prompt-drafting starter. Audio generation is not connected yet.")

video = st.file_uploader("Optional: preview an MP4 clip", type=["mp4"])
if video is not None:
    st.video(video)
st.caption("The written description drives retrieval; this starter does not analyze video.")

scene = st.text_area(
    "Describe the setting and sounds you want",
    value="A rainy city alley at night with distant traffic.",
)
mood = st.selectbox("Choose a mood", ["Tense", "Calm", "Melancholic", "Joyful"])
audio_type = st.selectbox(
    "What are you creating?", ["Ambience", "Sound effect", "Instrumental music"]
)
duration = st.slider("Requested audio length (seconds)", 5, 20, 10)

# Avoid displaying a previous scene's results as if they match new inputs.
signature = (scene, mood, audio_type, duration)
if st.session_state.get("input_signature") != signature:
    for key in ("matches", "chosen_ids", "prompt_draft"):
        st.session_state.pop(key, None)
    st.session_state["input_signature"] = signature

data_path = Path(__file__).resolve().parent / "data" / "sound_descriptions.csv"
records = load_sound_descriptions(data_path)

if st.button("1. Find sound ideas"):
    st.session_state.pop("chosen_ids", None)
    st.session_state.pop("prompt_draft", None)
    try:
        st.session_state["matches"] = retrieve_examples(scene, records, audio_type)
    except ValueError as error:
        st.error(str(error))

matches = st.session_state.get("matches", [])
chosen = []
if "matches" in st.session_state:
    if matches:
        st.write("Suggested text references")
        st.dataframe(
            [{"description": row["description"], "similarity": round(row["score"], 3)}
             for row in matches],
            hide_index=True,
        )
        lookup = {row["id"]: row for row in matches}
        ids = st.multiselect(
            "Keep only ideas that fit your scene (optional)",
            options=list(lookup),
            format_func=lambda sound_id: lookup[sound_id]["description"],
            key="chosen_ids",
            on_change=lambda: st.session_state.pop("prompt_draft", None),
        )
        chosen = [lookup[sound_id] for sound_id in ids]
        st.caption("Similarity is vocabulary overlap, not confidence. Check exclusions yourself.")
    else:
        st.info("No matching references found. You can still draft from your description.")

if st.button("2. Build editable prompt"):
    try:
        st.session_state["prompt_draft"] = build_prompt(
            scene, mood, audio_type, duration, chosen
        )
        # TEAM TASK: optionally call the frontier LLM here to refine the local draft.
        # Keep the original scene constraints and require user review of the result.
    except ValueError as error:
        st.error(str(error))

if "prompt_draft" in st.session_state:
    prompt = st.text_area("3. Review and edit your prompt", key="prompt_draft", height=220)
    st.download_button(
        "Download prompt", data=prompt, file_name="scenesound_prompt.txt", mime="text/plain"
    )
    # TEAM TASK: add an explicit Generate audio button using the edited prompt.
    # TEAM TASK: retrieve the finished audio, then create a preview with FFmpeg.
