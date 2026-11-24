"""Run using: python -m streamlit run app.py"""

import streamlit as st
from pathlib import Path
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

# Reset retrieval and prompt inputs.
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
        st.caption("Similarity is based on vocabulary overlap, not confidence.")
    else:
        st.info("No matching references found. You can still draft from your description.")

if st.button("2. Build editable prompt"):
    try:
        st.session_state["prompt_draft"] = build_prompt(
            scene, mood, audio_type, duration, chosen
        )
    except ValueError as error:
        st.error(str(error))

if "prompt_draft" in st.session_state:
    prompt = st.text_area(
        "3. Review and edit your prompt before submitting",
        key="prompt_draft",
        height=220,
    )
    st.download_button(
        "Download prompt", data=prompt,
        file_name="scenesound_prompt.txt", mime="text/plain",
    )

    # Member 3 & 4: preserve the existing job until it has been retrieved.
    pending = "stable_audio_generation_id" in st.session_state
    if st.button(
        "4. Generate audio with Stable Audio",
        disabled=pending or not prompt.strip(),
    ):
        try:
            api_key = st.secrets["STABILITY_API_KEY"]
            generation_id = start_audio_generation(
                prompt=prompt, duration=duration, api_key=api_key,
            )
            st.session_state["stable_audio_generation_id"] = generation_id
            # Save what was actually submitted, not what inputs say later.
            st.session_state["audio_request"] = {
                "prompt": prompt,
                "duration": duration,
                "signature": signature,
            }
            # Keep the previous completed audio while this request runs.
            st.success("Audio generation submitted. Use Check status to retrieve it.")
        except (FileNotFoundError, KeyError):
            st.error("Add STABILITY_API_KEY to .streamlit/secrets.toml.")
        except (StableAudioError, ValueError) as error:
            st.error(str(error))

# Outside prompt condition, a job can still be checked after the user changes the scene or clears/rebuilds the prompt.
if "stable_audio_generation_id" in st.session_state:
    st.info("An audio request is pending. Check it before submitting another.")

    if st.button("Check Stable Audio status"):
        try:
            api_key = st.secrets["STABILITY_API_KEY"]
            job_id = st.session_state["stable_audio_generation_id"]
            audio_bytes = fetch_audio_result(job_id, api_key)

            if audio_bytes is None:
                st.info("Audio is still generating. Check again later.")
            else:
                st.session_state["audio_result"] = {
                    **st.session_state.get("audio_request", {}),
                    "data": audio_bytes,
                    "filename": "scenesound_generated.mp3",
                    "mime": "audio/mpeg",
                    "source": "generated",
                    "generation_id": job_id,
                }
                st.session_state.pop("stable_audio_generation_id", None)
                st.session_state.pop("audio_request", None)
                # Refresh the Generate button's disabled state.
                st.rerun()
        except (FileNotFoundError, KeyError):
            st.error("Add STABILITY_API_KEY to .streamlit/secrets.toml.")
        except (StableAudioError, ValueError) as error:
            # Keep both the job ID and the last completed audio on an error.
            st.error(str(error))

    with st.expander("Trouble retrieving this request?"):
        st.warning(
            "If this request is no longer retrievable, you can forget it. "
            "This does not cancel generation on Stability's servers. "
            "A new generation may use additional credits."
        )

        if st.button("Forget pending request"):
            st.session_state.pop("stable_audio_generation_id", None)
            st.session_state.pop("audio_request", None)
            st.rerun()

# Member 4: this player remains visible even when no prompt draft is present.
if "audio_result" in st.session_state:
    result = st.session_state["audio_result"]
    st.subheader("Last completed audio")

    if result.get("source") == "generated":
        st.caption("Generated with Stable Audio.")
    else:
        # A result left over from an older app version may lack metadata.
        st.caption("Previously saved audio; source details are unavailable.")

    if "duration" in result:
        st.caption(f"Requested length: {result['duration']} seconds.")

    if "signature" not in result or "prompt" not in result:
        st.info("The original request details are unavailable for this saved result.")
    elif (
        result["signature"] != signature
        or result["prompt"] != st.session_state.get("prompt_draft")
    ):
        st.info(
            "This audio belongs to an earlier request. Generate again when "
            "you are ready to update it."
        )

    st.audio(result["data"], format=result["mime"])
    st.download_button(
        "Download audio", data=result["data"],
        file_name=result["filename"], mime=result["mime"],
    )

# Test audio uses a separate state key so it cannot replace generated audio.
if st.button("Load test audio (no API call)"):
    audio_path = Path(__file__).resolve().parent / "data" / "test_audio.mp3"
    try:
        test_bytes = audio_path.read_bytes()
        if not test_bytes:
            raise ValueError("The test MP3 is empty. Please use a playable MP3.")
        st.session_state["test_audio_result"] = test_bytes
    except OSError:
        st.error("Could not read data/test_audio.mp3. Check the file and permissions.")
    except ValueError as error:
        st.error(str(error))

if "test_audio_result" in st.session_state:
    st.subheader("Test audio — not AI-generated")
    st.audio(st.session_state["test_audio_result"], format="audio/mpeg")
    st.download_button(
        "Download test audio", data=st.session_state["test_audio_result"],
        file_name="scenesound_test.mp3", mime="audio/mpeg",
    )

# Members 5/6: later add a combined video/audio preview using FFmpeg.
