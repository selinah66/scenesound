"""Run from this folder with: python -m streamlit run app.py"""

from pathlib import Path

import streamlit as st

from mvp.nlp import load_sound_descriptions, retrieve_examples
from mvp.prompts import build_prompt

from mvp.audio import (
    StableAudioError,
    start_audio_generation,
    fetch_audio_result,)

st.set_page_config(page_title="SceneSound starter", page_icon="🎬", layout="centered")
st.title("SceneSound")
st.caption("Draft scene-based audio prompts, then generate and download soundtracks using Stable Audio.")

video = st.file_uploader("Optional: preview an MP4 clip", type=["mp4"])
if video is not None:
    st.video(video)
st.caption("The written description drives retrieval and this starter does not analyze video yet.")

scene = st.text_area(
    "Describe the setting and sounds you want",
    value="A rainy city alley at night with distant traffic.",
)
mood = st.selectbox("Choose a mood", ["Tense", "Calm", "Melancholic", "Joyful", "Urgent"])
audio_type = st.selectbox(
    "What are you creating?", ["Ambience", "Sound effect", "Instrumental music"]
)
duration = st.slider("Requested audio length (seconds)", 5, 20, 10)

# Avoid displaying a previous scene's results as if they match new inputs.
signature = (scene, mood, audio_type, duration)
if st.session_state.get("input_signature") != signature:
    for key in ("matches", "chosen_ids", "prompt_draft", "stable_audio_generation_id", "audio_result"):
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
        st.caption("Similarity is based on vocabulary overlap, not confidence.")
    else:
        st.info("No matching references found. You can still draft from your description.")

if st.button("2. Build editable prompt"):
    try:
        st.session_state.pop("stable_audio_generation_id", None)
        st.session_state.pop("audio_result", None)
        st.session_state["prompt_draft"] = build_prompt(
            scene, mood, audio_type, duration, chosen
        )
        # TEAM TASK: optionally call the frontier LLM here to refine the local draft.
        # Keep the original scene constraints and require user review of the result.
    except ValueError as error:
        st.error(str(error))

if "prompt_draft" in st.session_state:
    prompt = st.text_area("3. Review and edit your prompt before submitting", key="prompt_draft", height=220)
    st.download_button(
        "Download prompt", data=prompt, file_name="scenesound_prompt.txt", mime="text/plain"
    )

# Member 3 work here

    # member 3: submit one audio generation only when clicked
    if st.button("4. Generate audio with Stable Audio"):
        try:
            api_key = st.secrets["STABILITY_API_KEY"]
            generation_id = start_audio_generation(
                prompt=st.session_state["prompt_draft"],
                duration=duration,
                api_key=api_key,
            )
            st.session_state["stable_audio_generation_id"] = generation_id
            st.session_state.pop("audio_result", None)
            st.success("Audio generation submitted. Use Check status to retrieve it.")
        except KeyError:
            st.error("STABILITY_API_KEY is missing from Streamlit secrets.")
        except (StableAudioError, ValueError) as error:
            st.error(str(error))

    # member 3: check an existing job without generating another
    if "stable_audio_generation_id" in st.session_state:
        st.caption("Generation submitted. Checking status does not use generation credits.")
        if st.button("Check Stable Audio status"):
            try:
                api_key = st.secrets["STABILITY_API_KEY"]
                audio_bytes = fetch_audio_result(
                    st.session_state["stable_audio_generation_id"],
                    api_key,)

                if audio_bytes is None:
                    st.info("Audio is still generating. Check again later.")
                else:
                    st.session_state["audio_result"] = {
                        "data": audio_bytes,
                        "filename": "scenesound_generated.mp3",
                        "mime": "audio/mpeg",}

                    st.success("Your generated audio is ready.")
            except KeyError:
                st.error("STABILITY_API_KEY is missing from Streamlit secrets.")
            except (StableAudioError, ValueError) as error:
                st.error(str(error))

# Temporary test button — does not call Stable Audio.
    if st.button("Load test audio"):
        audio_path = Path(__file__).resolve().parent / "data" / "test_audio.mp3"

        try:
            st.session_state["audio_result"] = {
                "data": audio_path.read_bytes(),
                "filename": "scenesound_test.mp3",
                "mime": "audio/mpeg",
            }
        except FileNotFoundError:
            st.error("Please add an MP3 file at data/test_audio.mp3.")

    # Display saved audio on every rerun.
    if "audio_result" in st.session_state:
        result = st.session_state["audio_result"]

        st.audio(
            result["data"],
            format=result["mime"],)

        st.download_button(
            "Download audio",
            data=result["data"],
            file_name=result["filename"],
            mime=result["mime"],)

    # Member #5/6: retrieve the finished audio, then create a preview with FFmpeg.
