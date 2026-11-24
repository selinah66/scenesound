"""Legacy implementation. The current app uses mvp/audio.py."""

import time

import requests

API_URL = "https://api.stability.ai/v2beta/audio"


def generate_audio(prompt, duration, api_key, timeout=180):
    """Return the finished MP3, or raise RuntimeError with a message for the user."""
    headers = {"authorization": f"Bearer {api_key}", "accept": "audio/*"}
    try:
        # 1. Send the prompt. Stable Audio answers with an ID number for this job.
        started = requests.post(
            f"{API_URL}/stable-audio/text-to-audio",
            headers=headers,
            files={"none": ""},
            data={"prompt": prompt, "duration": duration, "output_format": "mp3"},
            timeout=30,)
        if started.status_code != 202:
            raise RuntimeError(f"Stable Audio refused the request: {started.text}")
        generation_id = started.json()["id"]

        # 2. Check the status every 5 seconds until it is ready or time runs out.
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            result = requests.get(
                f"{API_URL}/results/{generation_id}", headers=headers, timeout=30)
            if result.status_code == 200:
                return result.content  # 3. The finished audio.
            if result.status_code != 202:
                raise RuntimeError(f"Stable Audio could not finish: {result.text}")
            time.sleep(5)
    except (requests.RequestException, KeyError, ValueError) as error:
        raise RuntimeError(
            "Could not reach Stable Audio. Check your internet and try again.") from error
    raise RuntimeError("Stable Audio took too long. Please try again.")