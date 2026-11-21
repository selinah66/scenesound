# SceneSound

A TAC 459 team project that helps filmmakers turn a written scene description
into an editable audio prompt and, eventually, a generated soundscape.

The current version is a working local NLP and prompt-drafting starter. Stable
Audio generation, generated-audio playback/download, and combined video/audio
export are planned and are not implemented in the latest code reviewed for
this README.

## Current features

- Upload and display an optional MP4 clip.
- Enter a scene description, mood, audio type, and requested duration.
- Retrieve sound-description references using TF-IDF and cosine similarity.
- Let the user choose references; none are selected automatically.
- Build, edit, and download a text prompt.

The current app uses the written description, not automatic video analysis.
No API key, model-weight download, FFmpeg installation, or paid request is
needed for the features above.

## Planned MVP workflow

1. Enter a scene description and choose audio settings.
2. Retrieve and select relevant text references.
3. Build and edit the audio prompt.
4. Click **Generate audio** to submit the edited prompt to Stable Audio.
5. Play and download the generated result.

Stable Audio is the proposed external AI API. Gemini is not part of the current
plan: the team's Python code constructs the prompt directly. Confirm with the
instructor that Stable Audio satisfies the course's frontier-model API
requirement. TF-IDF retrieval demonstrates NLP concepts but is not an LLM.

Video/audio assembly with FFmpeg is a later extension once the core workflow
works.

## Setup

Use Python 3.11 or newer; Python 3.12 is recommended. Open a terminal in the
folder containing `app.py` and `requirements.txt`.

Create a virtual environment:

```bash
python -m venv .venv
```

On macOS/Linux, use `python3` instead if `python` is unavailable.

Activate it on macOS/Linux:

```bash
source .venv/bin/activate
```

Or activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies and launch:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL printed in the terminal, normally `http://localhost:8501`.
Run from the project root so that the `mvp` imports and data paths resolve.

## How to use the current version

1. Optionally upload an MP4 for visual reference.
2. Describe the setting and desired sounds.
3. Choose a mood, audio type, and duration.
4. Click **Find sound ideas** and select any useful descriptions.
5. Click **Build editable prompt**.
6. Review the text, make changes, and download the prompt.

Changing the scene or settings clears the previous prompt draft. Download any
edits you want to keep before changing inputs or rebuilding the prompt.

## Code and data

Read the files in this order:

1. `data/sound_descriptions.csv`: a small text collection for retrieval. The
   starter examples were AI-authored; the team should review, revise, and expand
   them and record the provenance of any additions.
2. `mvp/nlp.py`: loads descriptions, preprocesses text, fits TF-IDF on the
   reference collection, and ranks matches within the selected audio type.
3. `mvp/prompts.py`: combines user inputs and explicitly selected references
   into a prompt template.
4. `app.py`: connects the functions to Streamlit widgets and session state.

The CSV requires these columns:

| Column | Purpose |
| --- | --- |
| `id` | Unique identifier for each description |
| `audio_type` | `Ambience`, `Sound effect`, or `Instrumental music` |
| `description` | A short description of the sound |

This CSV is a retrieval collection, not recorded audio or training data for
Stable Audio. A small team-written collection is sufficient for initial
experiments; no audio dataset is required for this retrieval step.

## Course concepts

The starter adapts text preprocessing and TF-IDF concepts from the supplied
Class 2 and Class 3 notebooks. Comments in `mvp/nlp.py` identify the relevant
sections: Class 2 sections 2.2 and 2.4, and Class 3 sections 3.1.2 and 3.1.

SceneSound-specific additions include audio-type filtering, ranking references,
user selection, prompt construction, and interface integration. The team should
understand and explain these adaptations and follow the course's guidance on
writing the MVP mostly themselves.

## Team MVP responsibilities

| Member | Responsibility |
| --- | --- |
| 1 | Review and finish preprocessing and TF-IDF retrieval; curate the sound-description CSV. |
| 2 | Improve prompt construction and check that users can review and edit the prompt before generation. |
| 3 | Connect Stable Audio: submit requests, track generation IDs, check completion with a timeout, and retrieve audio. |
| 4 | Add playback and download; preserve audio in session state without triggering another generation. |
| 5 | Integrate the functions into Streamlit and check functionality on desktop and mobile browsers. |
| 6 | Design the UI/UX with Member 5, lead usability testing, deploy the website, and create the QR code. |

Each member should document their own functions and setup requirements. Use
branches and pull requests to review and combine changes.

For the audio handoff, use the final edited prompt and send duration separately
as an API parameter. Keep generation inside an explicit button action. Save
the completed audio, format, prompt, and duration in session state; display the
player and download button outside the generation button block. Clearly label
older audio when the request changes, and retain it if a new request fails.
Session state is not permanent storage.

Member 4 can test with a permitted local MP3 before the API is connected. Label
that as test audio rather than presenting it as generated output.

## Prototype directions

After completing the shared MVP, each pair builds a small working prototype:

- **Pair 1 — Prompting:** add an "Other" mood, prompt enhancement, and a way to
  clarify or edit requests.
- **Pair 2 — Iteration:** collect feedback after playback and generate a revised
  version closer to the user's request.
- **Pair 3 — Comparison:** compare two audio versions with the same short video,
  starting with different styles from the same model.

The team will select one prototype and improve it into the final product,
explaining the choice and tradeoffs.

## API keys and configuration

The current local features do not use credentials. When the Stable Audio
integration is added, read the key from environment variables or Streamlit
secrets. A `.env.example` file contains placeholders only; it does not make the
app load `.env` automatically.

For local Streamlit secrets, the planned configuration is:

```toml
# .streamlit/secrets.toml — local only; do not commit
STABILITY_API_KEY = "YOUR_API_KEY"
```

Add `.env`, `.venv/`, and `.streamlit/secrets.toml` to `.gitignore` if not already
excluded. Never put real keys in source code, the CSV, screenshots, or commits.
For deployment, configure secrets in the hosting platform's settings.

## Sharing during development

The local app has been run successfully and shared through a temporary
Cloudflare tunnel. To start a tunnel after installing `cloudflared`, keep
Streamlit running and run this in a second terminal:

```bash
cloudflared tunnel --url http://localhost:8501
```

Share the generated `trycloudflare.com` URL. Keep both processes running and
the laptop awake and connected. This is temporary sharing, not a permanent
deployment. Once paid generation is enabled, people with access to the app may
be able to spend the configured API credits.

The final product should have a deployed website, a mobile-friendly page, and
a QR code. A native App Store or Google Play app is not required by the updated
course guidance.

## Limitations and checks

- TF-IDF matches vocabulary, not meaning. It can miss synonyms or suggest
  inappropriate references.
- Similarity scores are not probabilities or confidence estimates.
- Keeping stop words does not make retrieval understand negation: "no traffic"
  may still retrieve traffic descriptions. Users must review the results.
- Mood is user-selected; no mood or sentiment classifier is implemented.
- Requested duration is not yet checked against the uploaded video's duration.
- The app does not yet synchronize or mix video and generated audio.
- Check blank input, no-overlap queries, audio-type filtering, selected
  references, manual prompt edits, and prompt downloads.
- Once audio is connected, verify that playback, downloads, and ordinary widget
  changes do not trigger another API request.
- Keep routine uploads and generated media out of Git. Include only small,
  deliberately selected examples with permission and attribution.

## Verification status

The local Streamlit app has been run successfully. Earlier checks exercised
retrieval and prompt construction for relevant queries, no-overlap queries,
blank input, audio-type filtering, ranking, and preservation of scene text.
These checks do not establish audio quality or complete end-to-end operation.

No completed Stable Audio API integration or combined video/audio export is
present in the latest code reviewed. Record live API and media tests here as
the team implements them.

## References

- [scikit-learn: TfidfVectorizer](https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html)
- [scikit-learn: cosine_similarity](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html)
- [Streamlit: file uploader](https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader)
- [Streamlit: session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state)
- [Streamlit: audio playback](https://docs.streamlit.io/develop/api-reference/media/st.audio)
- [Streamlit: download button](https://docs.streamlit.io/develop/api-reference/widgets/st.download_button)
- [Stability AI: text-to-audio API](https://docs.stability.ai/api-reference/stable-audio/text-to-audio)
- [Cloudflare: Quick Tunnels](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/)

## Audio attribution

The following attribution is retained for the referenced test music. This
credit does not identify the track as SceneSound-generated audio.

Echoes by Scott Buckley | www.scottbuckley.com.au  
Music promoted by https://www.chosic.com/free-music/all/  
Creative Commons CC BY 4.0  
https://creativecommons.org/licenses/by/4.0/
