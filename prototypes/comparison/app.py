"""SceneSound A/B comparison prototype. Run: streamlit run app.py"""
from __future__ import annotations

import hashlib
import os

from audio import StableAudioError, fetch_audio_result, start_audio_generation

import streamlit as st
from preview import PreviewError, create_preview

st.set_page_config(page_title="SceneSound | A/B Comparison", layout="wide")
st.title("SceneSound — A/B Soundtrack Comparison")
st.caption("Compare two audio styles against the same video clip.")

STYLES = ["Sparse piano", "Low strings", "Ambient electronic", "Minimal percussion", "Cinematic orchestral", "Custom"]


def init_state() -> None:
    for label in ("A", "B"):
        for field in ("preview", "signature", "job_id", "generated_audio", "submitted_prompt", "submitted_duration", "generation_error"):
            st.session_state.setdefault(f"{label}_{field}", None)
    st.session_state.setdefault("preference", "No preference")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_api_key() -> str | None:
    """Read a credential from Streamlit secrets or the environment, never source code."""
    try:
        key = st.secrets.get("STABILITY_API_KEY")
    except (FileNotFoundError, KeyError):
        key = None
    return (key or os.environ.get("STABILITY_API_KEY") or "").strip() or None


init_state()
api_key = get_api_key()
if not api_key:
    st.info("To generate audio, configure STABILITY_API_KEY in Streamlit secrets or your environment. Manual audio uploads still work.")
video_file = st.file_uploader("Upload a short video", type=["mp4", "mov", "m4v"])
scene = st.text_input("Scene description", "A tense nighttime street scene")
duration = st.slider("Preview duration (seconds)", min_value=3, max_value=30, value=10)

if video_file is not None:
    st.video(video_file)

columns = st.columns(2)
for label, column in zip(("A", "B"), columns):
    with column:
        st.subheader(f"Version {label}")
        style = st.selectbox("Audio style", STYLES, index=0 if label == "A" else 1, key=f"style_{label}")
        prompt = st.text_area(
            "Generation prompt (editable)",
            value=f"{scene}. Instrumental soundtrack, {style.lower()}, no vocals.",
            key=f"prompt_{label}",
        )
        audio_file = st.file_uploader("Upload generated audio", type=["mp3", "wav", "m4a", "ogg", "flac"], key=f"audio_{label}")
        if audio_file is not None:
            st.audio(audio_file)

        # Each version owns its own generation ID and finished audio.
        job_key = f"{label}_job_id"
        generated_key = f"{label}_generated_audio"
        error_key = f"{label}_generation_error"
        submitted_prompt_key = f"{label}_submitted_prompt"
        submitted_duration_key = f"{label}_submitted_duration"

        if st.session_state[job_key] is not None:
            st.caption(f"Generation ID ({label}): {st.session_state[job_key]}")
            if st.session_state[generated_key] is None:
                st.info("Generation submitted. Click Check status to retrieve the result.")

        if st.session_state[error_key]:
            st.error(st.session_state[error_key])

        generation_col, status_col = st.columns(2)
        with generation_col:
            # Avoid submitting another job while an earlier one is pending.
            pending = (st.session_state[job_key] is not None
                       and st.session_state[generated_key] is None)
            if st.button(f"Generate audio {label}", key=f"generate_{label}",
                         disabled=not api_key or pending):
                try:
                    with st.spinner(f"Submitting version {label}..."):
                        generation_id = start_audio_generation(prompt, duration, api_key)
                    st.session_state[job_key] = generation_id
                    st.session_state[generated_key] = None
                    st.session_state[submitted_prompt_key] = prompt
                    st.session_state[submitted_duration_key] = duration
                    st.session_state[error_key] = None
                    st.session_state[f"{label}_preview"] = None
                    st.session_state[f"{label}_signature"] = None
                    st.rerun()
                except (StableAudioError, ValueError) as exc:
                    st.session_state[error_key] = str(exc)
                    st.error(str(exc))

        with status_col:
            pending = (st.session_state[job_key] is not None
                       and st.session_state[generated_key] is None)
            if st.button(f"Check status {label}", key=f"check_{label}",
                         disabled=not api_key or not pending):
                try:
                    with st.spinner(f"Checking version {label}..."):
                        result = fetch_audio_result(st.session_state[job_key], api_key)
                    if result is None:
                        st.info("Still processing. Check again in a few seconds.")
                    else:
                        st.session_state[generated_key] = result
                        st.session_state[error_key] = None
                        st.rerun()
                except (StableAudioError, ValueError) as exc:
                    # Keep the ID: network errors or rate limits should not cause resubmission.
                    st.session_state[error_key] = str(exc)
                    st.error(str(exc))

        generated_audio = st.session_state[generated_key]
        if generated_audio is not None:
            st.success(f"Version {label} generated successfully.")
            st.audio(generated_audio, format="audio/mp3")
            if (prompt != st.session_state[submitted_prompt_key]
                    or duration != st.session_state[submitted_duration_key]):
                st.warning("The generated track uses the earlier submitted prompt/duration, not the current edits.")

        # Uploaded audio overrides generated audio for the preview, when present.
        selected_audio = (audio_file.getvalue() if audio_file is not None
                          else generated_audio)
        if video_file is not None and selected_audio is not None:
            video_bytes = video_file.getvalue()
            signature = (digest(video_bytes), digest(selected_audio), duration)
            if st.session_state[f"{label}_signature"] != signature:
                st.session_state[f"{label}_preview"] = None
                st.session_state[f"{label}_signature"] = signature

            if st.button(f"Create preview {label}", key=f"create_{label}"):
                try:
                    with st.spinner(f"Rendering version {label}..."):
                        st.session_state[f"{label}_preview"] = create_preview(
                            video_bytes, selected_audio, duration
                        )
                except (PreviewError, ValueError) as exc:
                    st.error(str(exc))
        else:
            # Never show a preview from a previous video/audio selection.
            st.session_state[f"{label}_preview"] = None
            st.session_state[f"{label}_signature"] = None

        preview = st.session_state[f"{label}_preview"]
        if preview is not None:
            st.video(preview, format="video/mp4")
            st.download_button(
                f"Download version {label}",
                data=preview,
                file_name=f"scenesound_version_{label}.mp4",
                mime="video/mp4",
                key=f"download_{label}",
            )

st.divider()
st.radio("Which soundtrack works better?", ["A", "B", "No preference"], key="preference", horizontal=True)
st.caption(f"Current selection: {st.session_state['preference']}")
