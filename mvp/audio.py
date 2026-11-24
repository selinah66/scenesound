"""Member 3: submit Stable Audio jobs and retrieve their results.

No generation runs at import time. Call start_audio_generation only after an
explicit user action; status checks never submit another generation.
"""

import math
import re
import time

import requests


BASE_URL = "https://api.stability.ai/v2beta/audio"
REQUEST_TIMEOUT = (10, 60)


class StableAudioError(RuntimeError):
    """A generation or retrieval request failed."""

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


def _headers(api_key):
    # keep credentials in request headers rather than urls or logs
    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("A Stability API key is required.")
    return {
        "Authorization": f"Bearer {api_key.strip()}",
        "Accept": "audio/*",
    }


def _validate_id(generation_id):
    # reject invalid ids before constructing a results url
    if not isinstance(generation_id, str) or not re.fullmatch(
        r"[0-9a-fA-F]{64}", generation_id
    ):
        raise ValueError("Expected a 64-character hexadecimal generation ID.")


def _raise_api_error(response):
    # use safe messages rather than exposing response bodies or credentials
    messages = {
        400: "Invalid request. Check prompt and duration.",
        401: "Invalid or missing Stability API key.",
        402: "Insufficient Stability API credits.",
        403: "Request blocked by content moderation or access restrictions.",
        404: "Generation not found or expired. Check its ID and account.",
        413: "Request is too large.",
        422: "Stable Audio could not process these inputs.",
        429: "Rate limit reached. Wait before checking again.",
    }
    message = messages.get(
        response.status_code,
        "Stability API request failed. Check service availability before retrying.",
    )
    raise StableAudioError(
        f"{message} (HTTP {response.status_code})", response.status_code
    )


def start_audio_generation(prompt, duration, api_key):
    """Submit one MP3 generation and return its ID; never retry a POST."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Enter a nonempty audio prompt.")
    prompt = prompt.strip()
    if len(prompt) > 10000:
        raise ValueError("Prompt must contain at most 10,000 characters.")
    if (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(duration)
        or not 1 <= duration <= 380
    ):
        raise ValueError("Duration must be between 1 and 380 seconds.")

    headers = _headers(api_key)
    try:
        # multipart fields send duration separately from prompt text
        response = requests.post(
            f"{BASE_URL}/stable-audio/text-to-audio",
            headers=headers,
            files={
                "prompt": (None, prompt),
                "duration": (None, str(duration)),
                "output_format": (None, "mp3"),
                "model": (None, "stable-audio-3"),
            },
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException:
        # acceptance may be uncertain after a network failure
        raise StableAudioError(
            "Submission connection failed or timed out. The request may have "
            "been accepted; do not automatically submit it again."
        ) from None

    if response.status_code != 202:
        _raise_api_error(response)
    try:
        generation_id = response.json()["id"]
        _validate_id(generation_id)
    except (ValueError, KeyError, TypeError):
        raise StableAudioError(
            "API accepted the request but returned no valid generation ID. "
            "Do not automatically resubmit."
        ) from None
    return generation_id


def fetch_audio_result(generation_id, api_key, *, timeout=REQUEST_TIMEOUT):
    """Return None for HTTP 202, or completed MP3 bytes for HTTP 200."""
    _validate_id(generation_id)
    headers = _headers(api_key)
    try:
        response = requests.get(
            f"{BASE_URL}/results/{generation_id}",
            headers=headers,
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException:
        raise StableAudioError(
            "Status check connection failed or timed out. Keep the generation "
            "ID and check it again; no new generation is needed."
        ) from None

    if response.status_code == 202:
        return None
    if response.status_code != 200:
        _raise_api_error(response)

    # Do not pass json errors or empty responses to an audio player
    content_type = (
        response.headers.get("Content-Type", "")
        .split(";")[0]
        .strip()
        .lower()
    )
    if not content_type.startswith("audio/") or not response.content:
        raise StableAudioError("API returned an empty or unexpected audio result.")
    return response.content


def wait_for_audio(generation_id, api_key, *, timeout_seconds=300, poll_seconds=10):
    """Optionally poll an existing job; retain its ID if the wait times out.

    For Streamlit, fetch_audio_result supports a nonblocking Check status button.
    This helper is intended for scripts or an explicitly requested bounded wait.
    """
    _validate_id(generation_id)
    _headers(api_key)
    for name, value in (("timeout_seconds", timeout_seconds), ("poll_seconds", poll_seconds)):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"{name} must be a finite positive number.")

    deadline = time.monotonic() + timeout_seconds
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(
                "Stopped waiting for audio. The generation may still be running; "
                "check the same generation ID again."
            )
        audio = fetch_audio_result(
            generation_id, api_key, timeout=min(60, remaining)
        )
        if audio is not None:
            return audio
        time.sleep(min(poll_seconds, max(0, deadline - time.monotonic())))
