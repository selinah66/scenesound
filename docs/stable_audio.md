# Member 3: Stable Audio integration

`mvp/audio.py` implements prompt submission, generation-status checks, and audio
retrieval through the official Stable Audio 3 asynchronous REST API. There is no
Gemini dependency in this module. Member 1's retrieval work can finish separately.

## Setup

Install requirements with `python -m pip install -r requirements.txt`. Obtain a
Stability API key and sufficient credits from https://platform.stability.ai/.
For Streamlit, store the key in local `.streamlit/secrets.toml`:

```toml
STABILITY_API_KEY = "your-key-here"
```

That path is already ignored by Git. On Streamlit Community Cloud, add the same
setting in the deployment's Secrets settings. A GitHub Actions secret is not
automatically available to a running Streamlit app. Never commit a real key.

## Interface and team handoff

```python
from mvp.audio import start_audio_generation, fetch_audio_result, StableAudioError

# member 2 supplies final edited text and duration in seconds
# call only in response to an explicit generate button
job_id = start_audio_generation(edited_prompt, duration, api_key)

# members 4 and 5 save job_id in session state immediately
# later status checks must reuse this id rather than calling start again
audio_bytes = fetch_audio_result(job_id, api_key)

if audio_bytes is None:
    print("Still processing; check again in about 10 seconds.")
else:
    # member 4 stores audio_bytes in session state for playback and download
    print("Audio ready")
```

Member 5 should get `api_key` from `st.secrets["STABILITY_API_KEY"]` and handle
missing secrets with a setup message. Member 4 can pass completed bytes to
`st.audio(audio_bytes, format="audio/mpeg")` and `st.download_button` with
`mime="audio/mpeg"` and a `.mp3` filename. Do not call APIs merely because
Streamlit reruns. Keep the submitted prompt, duration, ID, and bytes together so
an older result is clearly associated with its original inputs.

Optional script polling:

```python
from mvp.audio import wait_for_audio

# this waits for an existing job and never submits another generation
audio_bytes = wait_for_audio(job_id, api_key, timeout_seconds=300, poll_seconds=10)
```

The wait uses a polling deadline and network timeouts. A request already in
flight can outlast the remaining polling interval. A timeout stops local waiting;
it does not cancel a remote generation. Keep its ID and fetch it again. API
results are retained for 24 hours, so download completed audio promptly.

## Expected responses and errors

- POST `/v2beta/audio/stable-audio/text-to-audio` returns HTTP 202 with an ID.
- GET `/v2beta/audio/results/{id}` returns HTTP 202 while processing, or HTTP 200
  with audio bytes when complete. Both requests use the same account API key.
- Duration is sent separately as a multipart field, not only embedded in text.
- `ValueError` means an invalid local input; no request is made.
- `StableAudioError` contains a safe message and optional `status_code` for UI
  handling. HTTP 401 means a key problem, 402 insufficient credits, 404 a missing
  or expired job, and 429 rate limiting. Let users wait before another GET.
- After a POST connection failure, acceptance is uncertain. No POST is retried
  automatically, avoiding an accidental duplicate paid generation. After a GET
  failure, keep the ID and check it again.

## Verification

Run offline tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

All 14 offline tests passed. Tests mock HTTP responses and cover multipart submission, pending/completed
results, validation, errors, uncertain submission, and polling timeout. They do
not demonstrate a live successful generation. A live check still requires a real
key and credits: submit one 10-second prompt, retain its ID, fetch until complete,
and listen to the downloaded MP3. No live API request has been run for this change.

This branch implements Member 3's backend. It deliberately leaves the shared
Streamlit page, playback/download UI, preprocessing, and prompt builder to their
assigned members. Audio/video combining is also outside this change.

## Sources

- https://docs.stability.ai/api-reference/stable-audio/text-to-audio
- https://docs.stability.ai/api-reference/audio-results/fetch-audio-result
- https://docs.stability.ai/api-reference

This API integration is new project code, not a claim of copied course code.
