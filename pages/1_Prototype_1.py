"""Pair 1 · Independent sound directions and a synchronized audition mixer."""
import base64
import json
import os
from pathlib import Path
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

from mvp.audio import StableAudioError, start_audio_generation, fetch_audio_result
from mvp.layers import QUALITIES, demo, direction
from mvp.mood import mood_direction, suggest_point
from mvp.mood_map import mood_map

st.set_page_config(page_title="Prototype 1 · SceneSound", layout="wide")
st.title("Prototype 1")
state = st.session_state
scene = st.text_area("Scene description", "A figure crosses a rainy alley and stops at a door.")
recommended = suggest_point(scene)
if state.get("mood_scene") != scene:
    state.mood_scene = scene
    state.mood_revision = state.get("mood_revision", 0) + 1
    state.tone, state.energy = recommended
st.subheader("Scene atmosphere")
st.caption("Your description sets the starting point. Move the dot or adjust either slider to direct the sound.")
map_col, settings = st.columns([1, 1.8], gap="large", vertical_alignment="center")
map_key = f"mood_map_{state.mood_revision}"


def apply_map():
    state.tone, state.energy = state[map_key]


def restore_suggestion():
    state.tone, state.energy = recommended


with map_col:
    mood_map(current=[state.tone, state.energy], default=recommended,
             key=map_key, on_change=apply_map)
with settings:
    tone_col, energy_col, reset_col = st.columns([1, 1, 1], vertical_alignment="center")
    tone_col.slider("Dark → Bright", -100, 100, key="tone")
    energy_col.slider("Still → Driven", -100, 100, key="energy")
    reset_col.button("Use suggested mood", on_click=restore_suggestion)
    mood = mood_direction(state.tone, state.energy)
    st.caption(mood)
    nuance = st.text_input("Additional mood direction (optional)", placeholder="e.g. nostalgic, with a hint of relief")
    if nuance.strip():
        mood += f". {nuance.strip()}"
    duration = st.slider("Soundtrack length (seconds)", 5, 20, 10)
video = st.file_uploader("Optional scene video · MP4, up to 25 MB", type=["mp4"], max_upload_size=25)
mode = st.radio("Generation source", ["Local sound demo", "Stable Audio"], horizontal=True)
if mode == "Local sound demo":
    st.caption("Synthesized rain, footsteps and music demonstrate intensity changes. Use Stable Audio for custom text directions.")


def track(category, name, notes, ready=False):
    result = dict(id=uuid4().hex, category=category, name=name, notes=notes)
    if ready:
        result.update(audio=demo(category, 1, 10, 0), mime="audio/wav", source="Local demo")
    return result


if "layer_tracks" not in state:
    state.layer_tracks = [track("Ambience", "Rain", "Steady rain on concrete.", True),
                          track("Action & Foley", "Footsteps", "Shoes hitting wet pavement.", True)]
tracks = state.layer_tracks
for item in tracks.copy():
    k = item["id"]
    category = item["category"]
    with st.expander(f"{category} · {item['name']}", expanded=True):
        name = st.text_input("Track name", item["name"], key=k+"name")
        item["name"] = name
        notes = st.text_input("Sound direction", item["notes"], key=k+"notes")
        level = st.select_slider("Performance intensity", options=[0, 1, 2], value=1,
                                 format_func=["Subtle", "Moderate", "Intense"].__getitem__, key=k+"level")
        draft = direction(scene, mood, category, name, notes, level)
        if item.get("draft") != draft:
            state[k+"prompt"] = draft
            item["draft"] = draft
        prompt = st.text_area("Generation prompt", key=k+"prompt",
                              help="Edit after setting the direction. Changing direction rebuilds this draft.")
        pending = item.get("job")
        if st.button("Regenerate track" if "audio" in item else "Generate track", key=k+"render",
                     disabled=bool(pending) or not all(x.strip() for x in (scene,mood,name,prompt))):
            if mode == "Local sound demo":
                item.update(audio=demo(category, level, duration, int(k[:8],16)), mime="audio/wav", source="Local demo")
                st.rerun()
            else:
                try:
                    key = os.getenv("STABILITY_API_KEY") or st.secrets["STABILITY_API_KEY"]
                    item["job"] = start_audio_generation(prompt, duration, key)
                except (KeyError, FileNotFoundError, ValueError, StableAudioError) as error:
                    st.error(str(error))
                else:
                    st.rerun()
        if pending:
            st.info("Generation pending. Your previous take is still available.")
            if st.button("Check generation", key=k+"check"):
                try:
                    key = os.getenv("STABILITY_API_KEY") or st.secrets["STABILITY_API_KEY"]
                    data = fetch_audio_result(pending, key)
                    if data is None:
                        st.info("Still generating.")
                    else:
                        item.update(audio=data, mime="audio/mpeg", source="Stable Audio")
                        del item["job"]
                        st.rerun()
                except (KeyError, FileNotFoundError, ValueError, StableAudioError) as error:
                    st.error(str(error))
            if st.button("Forget pending job", key=k+"forget", help="Does not cancel the provider request."):
                del item["job"]
                st.rerun()
        if st.button("Remove track", key=k+"remove", disabled=bool(pending)):
            tracks.remove(item)
            st.rerun()

category = st.selectbox("New track category", list(QUALITIES))
if st.button("Add track"):
    tracks.append(track(category, category, ""))
    st.rerun()

st.subheader("Audition mix")
def encoded(data):
    return base64.b64encode(data).decode("ascii")

rows = [dict(id=x["id"], name=x["name"], source=x["source"], data=encoded(x["audio"]))
        for x in tracks if "audio" in x]
if rows:
    payload = json.dumps(dict(rows=rows, video=encoded(video.getvalue()) if video else None)).replace("<", "\\u003c")
    html = (Path(__file__).resolve().parents[1]/"mvp"/"mixer.html").read_text()
    components.html(html.replace("/*PAYLOAD*/", payload), height=(330 if video else 0)+100+84*len(rows), scrolling=True)
else:
    st.info("Generate a track to hear the mix.")
