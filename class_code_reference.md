# SceneSound starter: references to the supplied class code

## What the current starter actually adapts

The class notebooks teach text preprocessing and numerical text features. This
starter applies those techniques to retrieving sound-description examples.
It does not claim that the notebooks already implement SceneSound or its APIs.
Cell indices below refer to zero-based positions in the notebook JSON `cells`
array, including Markdown cells; they are not execution counts. Navigate by
section title when opening the notebooks in Jupyter or Colab.

| Course source | Exact location | Connection to the starter |
| --- | --- | --- |
| `Class_2_TAC_459_Demo (1)(1).ipynb` | Section 2.2, Text Cleaning and Preprocessing; cell 21 | Lowercasing and regex cleaning inform `preprocess_text()` in `scenesound/nlp.py`. |
| Same Class 2 notebook | Section 2.4, Feature Extraction Techniques, subsection TF-IDF Using Scikit-Learn; cells 34 and 36 | The `TfidfVectorizer()` / `fit_transform(documents)` pattern is adapted for the sound-description collection. |
| `Class_3_TAC_459_Demo(1).ipynb` | Section 3.1.2, `preprocess_text`; cell 22 | The reusable preprocessing-function structure is adapted for scene descriptions. |
| Same Class 3 notebook | Section 3.1, TF-IDF vectorization; cell 28 | Reuses the text-to-feature-vector workflow. The demo's sentiment targets and classifier are not used. |

The Class 2 example includes:

```python
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(documents)
```

In SceneSound, `documents` becomes the descriptions in the CSV. We then transform
the new scene with that fitted vectorizer. Cosine-similarity ranking and filtering
by audio type are new application logic. No `cosine_similarity` call was found
in the code cells of these eight supplied notebooks; do not label that ranking
step as a verbatim class-code adaptation.

## Deliberate changes to preprocessing

- The Class 3 IMDB example removes English stop words. SceneSound keeps them:
  phrases such as 'no traffic' and 'without music' contain constraints.
- The class regex removes non-alphabetic characters. SceneSound retains digits
  and apostrophes and replaces other punctuation with spaces, to avoid joining
  words and to retain useful text such as timings in the retrieval copy.
- Normalization is applied consistently to reference descriptions and queries.
- The original scene string goes into the editable prompt unchanged; the
  normalized retrieval copy never overwrites it.
- The default TF-IDF analyzer still tokenizes text. Keeping text in preprocessing
  does not guarantee that every punctuation mark or single-character token is
  retained as a feature, or that negation is understood.

## Optional transformer extensions, not implemented in this starter

| Course source | Section / cell | Possible future use |
| --- | --- | --- |
| `Class_7_TAC_459_Demo(2).ipynb` | 7.2, contextual BERT embeddings; cells 45-46 and following embedding-function cell | Compare an embedding-based retrieval method against the TF-IDF baseline. Define pooling carefully and evaluate relevance. |
| Same Class 7 notebook | 7.5, BART zero-shot classification; cells 93 and 98 | Suggest a mood label from a scene description, with user override. Changing labels from the bias demo is an adaptation requiring evaluation, not a validated mood classifier. |
| `Class_3_TAC_459_Demo(1).ipynb` | 3.3; text-generation pipeline at cell 81 | Reference for loading a pretrained generator; not a completed scene-to-audio-prompt model. |
| `Class_4_TAC_459_Demo(1).ipynb` | 4.4, pretrained GPT-2 text generation | Another reference for tokenization and generation. Local generation is optional. |
| `Class_8_TAC_459_Demo(2).ipynb` | 8.6, GPT-2 Large; cells 100 and 105 | Reference for tokenizer/model loading, `generate()`, sampling controls, and decoding. This code is not run by the starter. |

An actual frontier-model API call remains a separate integration task. Running
TF-IDF, BERT, BART classification, or GPT-2 locally does not itself demonstrate
that API feature. The prompt builder currently uses a Python string template;
it does not call an LLM or generate sound.

## Material inspected but not needed for this small MVP

- Class 3: supervised sentiment classification and cross-validation.
- `Class_4_TAC_459_Demo(1).ipynb`: CNN/LSTM classification and lyric generation.
- `Class_5_TAC_459_Demo_P1_PyTorch(3).ipynb`: BERT classification training.
- `Class_5_TAC_459_Demo_P2_PyTorch(3).ipynb`: seq2seq summarization fine-tuning.
- Class 8: BERT classification, imbalance handling, LIME, and SHAP.
- `Class_9_TAC_459_Demo(2).ipynb`: translation training/inference and BLEU.

These techniques solve different tasks. They need not be added simply to
reference more classes. Keep the first workflow small and explain the parts
you actually implement. Do not reuse a positive/negative sentiment classifier
as a cinematic mood classifier without task-specific evidence.

## Public repository notes

Retain these source notes when adapting the starter. Do not automatically
publish full course notebooks, instructor datasets, or copied notebook outputs;
check what your course permits sharing. This ZIP includes references and a
small adaptation, not the uploaded notebooks or their embedded images.
