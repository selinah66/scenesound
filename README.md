# SceneSound: local NLP starter

A small starting point for the TAC 459 team MVP. This is **not the completed
MVP**: no frontier-model call, audio generation, or combined video/audio export
is implemented. The team's next task is to understand/adapt this code and
write the missing integrations in accordance with the course's MVP guidance.

## What works

- Display an optional MP4 clip (25 MB upload limit).
- Enter a scene, mood, audio type, and requested duration.
- Retrieve text references with TF-IDF and cosine similarity.
- Select appropriate references; none are selected automatically.
- Build, edit, and download a local prompt template.

No API keys, downloads of model weights, FFmpeg installation, or paid requests
are needed to run this starter. The video is displayed but not analyzed.

## Setup

Use Python 3.11 or newer; Python 3.12 is recommended.
Open a terminal in the folder that contains `app.py`.

```bash
python -m venv .venv
```

Activate the environment on macOS/Linux:

```bash
source .venv/bin/activate
```

Or activate it in Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Then install and launch:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On macOS/Linux, use `python3` for the first command if `python` is unavailable.
The UI launch opens a local web application. It does not deploy a public site.

## Read the code in this order

1. `data/sound_descriptions.csv`: 12 illustrative, AI-authored text examples,
   not recorded sounds, training labels, or an evaluated reference collection.
   Review and expand these with your team.
2. `scenesound/nlp.py`: fits TF-IDF on the reference collection and transforms
   a new scene description using the same vectorizer; ranks within audio type.
3. `scenesound/prompts.py`: creates a transparent draft from user inputs and
   references the user explicitly selected.
4. `app.py`: connects the functions to Streamlit widgets and session state.

The CSV is a retrieval collection, not a dataset for training an audio model.
Mood is explicitly user-selected; no sentiment/mood classifier is implemented.
The requested duration is not checked against video duration yet.

## Team implementation tasks

1. Revisit the matching class demos and explain or adapt the retrieval code.
   Decide whether retrieval actually improves SceneSound compared with using
   the scene description directly. Document the comparison honestly.
2. Implement a small real Gemini (or approved frontier LLM) API call after local
   prompt construction. Keep the original description and explicit exclusions;
   show the response for user editing. Choose a currently accessible model ID.
3. Add a **Generate audio** button that submits the edited prompt and a separate
   duration parameter to Stable Audio. Save the returned generation ID, poll
   for completion with a timeout, and retrieve the audio. Handle errors clearly.
   Do not trigger paid generation on every Streamlit rerun.
4. Probe video duration, install FFmpeg, and implement audio/video preview
   assembly. Define how to handle source audio, duration mismatch, and exports.
5. Test the complete workflow on a short permitted clip. Only then label it a
   completed MVP. Prototype alternatives and deployment follow later.

`.env.example` contains placeholders only. This starter does not load `.env`:
your integration must explicitly read environment variables or Streamlit
secrets. Never put real keys in the source code, CSV, screenshots, or commits.

## Limitations and useful checks

- TF-IDF is lexical retrieval, not semantic understanding. Vocabulary overlap
  can miss synonyms and return inappropriate references.
- Similarity scores are not probabilities or confidence estimates.
- Stop words are retained, but this does not make the system understand
  negation: 'no traffic' may still retrieve traffic. Users must review results.
- Blank input raises a clear error; a query with no vocabulary overlap returns
  no references rather than arbitrary ones.
- Try a rainy alley, a forest, an unrelated word, and a description excluding
  traffic. Check the differences and preserve the original user constraints.
- Small demo files belong in a deliberately curated examples folder; routine
  uploads and generated media are excluded by `.gitignore`.

## Verification of this starter

The Python files were syntax-checked, and local retrieval/prompt functions were
exercised for relevant queries, no-overlap queries, blank input, type filtering,
ranking, and preservation of original scene text. The Streamlit interface could
not be launched in the authoring environment because Streamlit was unavailable;
check it locally after installing the requirements. No live model or media-export
test has been performed because those features are intentionally unimplemented.

## References

- https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- https://scikit-learn.org/stable/modules/generated/sklearn.metrics.pairwise.cosine_similarity.html
- https://docs.streamlit.io/develop/api-reference/widgets/st.file_uploader
- https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state

Do not present this sample as code copied from your course demos; the exact
notebooks were not supplied for this starter. Map it to your actual coursework.
