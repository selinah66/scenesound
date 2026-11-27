"""Register the mood picker from a module Streamlit can identify."""
from pathlib import Path

from streamlit.components.v1 import declare_component

mood_map = declare_component("scene_mood_map", path=str(Path(__file__).resolve().parent))
