# Mini RAG-Powered Assistant

A Retrieval-Augmented Generation (RAG) assistant that answers questions from a custom document corpus. It retrieves the most relevant passages with vector similarity search and passes them to an LLM (Google Gemini) so answers are grounded in the documents, with sources shown for every answer.

The default corpus is the **MNIT Jaipur Institute Placement Policy** plus three small placement-related sample documents.

## Architecture

```
Browser (public/index.html)
        |  POST /api/ask
        v
Node.js + Express frontend  (src/server.js, port 3000)
        |  POST /ask
        v
Python FastAPI backend      (backend/main.py, port 8000)
        |
        |-- embed the question        -> Gemini embeddings (gemini-embedding-001)
        |-- similarity search (top 4) -> FAISS index (store/faiss.index)
        |-- build prompt with context -> Gemini chat model
        v
   { answer, sources }
```

**Offline indexing pipeline** (run once, or whenever documents change):

```
data/*.pdf|md|txt -> ingest.py (extract, clean, chunk) -> store/chunks.json
                  -> embed.py  (embeddings + FAISS)    -> store/faiss.index
```

### Why a hybrid (Python + Node.js) design

The brief asks for a Node.js frontend, while the RAG logic (parsing, embeddings, FAISS) has the most mature tooling in Python. The Node.js layer serves the UI and forwards questions to the Python API, so each part uses the language it is best suited for. The browser never sees the API key; only the Python backend talks to Gemini.

## Project structure

```
backend/
  ingest.py        # load PDFs/MD/TXT, clean noise, section-aware chunking
  embed.py         # embed chunks with Gemini, build and save FAISS index
  rag.py           # retrieve top-k chunks and generate a grounded answer
  main.py          # FastAPI app: GET /health, POST /ask
  search.py        # CLI to test retrieval without calling the LLM
  test_gemini.py   # quick check that the API key and models work
  requirements.txt
src/server.js      # Express server: serves UI, forwards /api/ask to Python
public/index.html  # simple web UI
data/              # the document corpus (4 documents)
store/             # generated chunks.json and faiss.index
```

## Corpus

| Document | Type | Notes |
|---|---|---|
| Institute_Placement_Policy-MNIT.pdf | PDF (12 pages) | Public MNIT Jaipur placement policy |
| Placement_FAQ.md | Markdown | Sample document created for this demo |
| Sample_Company_JNF_Nimbus.md | Markdown | Fictional company job notification form |
| Placement_Statistics_Report.md | Markdown | Fictional placement statistics |

The three Markdown documents are fictional and exist only to demonstrate multi-document retrieval.

## Key design choices

- **Section-aware chunking.** The policy has numbered sections (for example 5.1, 8.1). Text is split by section first, then into chunks of about 800 characters with 120 characters of overlap, cutting at sentence ends. This keeps each chunk about one topic.
- **Cleaning before embedding.** Repeated headers and footers ("Page 5 of 12"), the table of contents, and stray characters are removed so they do not pollute the embeddings.
- **Context in every chunk.** Each chunk is prefixed with its file name and section title, so the embedding knows where the text came from (important when different documents reuse section numbers).
- **Cosine similarity with FAISS.** Vectors are L2-normalised and stored in an exact `IndexFlatIP` index, so inner product equals cosine similarity. The corpus is small, so exact search is fast and needs no approximation.
- **Query vs document embeddings.** Gemini task types `RETRIEVAL_DOCUMENT` and `RETRIEVAL_QUERY` are used for chunks and questions respectively.
- **Grounded generation.** The system prompt tells the model to answer only from the supplied context, cite the document and section, and say so when the answer is not in the documents. Temperature is 0.2 for stable, factual answers.
- **Resilience.** API calls retry with backoff on rate limits (429) and temporary overload (503).

## Setup

### Prerequisites

- Python 3.10 to 3.12
- Node.js 20 or later
- A Gemini API key from [Google AI Studio](https://aistudio.google.com)

### 1. Clone and configure

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

Create a `.env` file in the project root (it is git-ignored):

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=your-gemini-chat-model-id
```

`GEMINI_MODEL` must be a model ID available to your key, in lowercase (for example a current Flash or Flash-Lite model).

### 2. Python backend

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt

python backend/ingest.py           # build store/chunks.json
python backend/embed.py            # build store/faiss.index
uvicorn main:app --app-dir backend --port 8000
```

### 3. Node.js frontend (new terminal)

```bash
npm install
npm start
```

Open http://localhost:3000 and ask a question.

### Optional: test retrieval from the command line

```bash
python backend/search.py "What is the 1.5X rule?"
```

## Example questions

- What is the 1.5X rule?
- When can I withdraw my company registration?
- How many red flags lead to debarment, and for how long?
- Is the Nimbus Data Analyst role a bonus profile? (combines the JNF and the policy)
- What was the median package for Computer Science? (statistics report)
- Who is the Prime Minister of India? (not in the documents, so the assistant should say it could not find an answer)

## Challenges faced and how they were resolved

| Challenge | Resolution |
|---|---|
| `Cannot use import statement outside a module` when running the first Node script | Added `"type": "module"` to `package.json` so Node treats the files as ES modules. |
| Gemini returned 404 because the chosen chat model was no longer available to new users | Switched to a currently available model and moved the model name to the `GEMINI_MODEL` environment variable so it can change without touching code. |
| 400 `unexpected model name format` | The model ID was written with capital letters. Model IDs are lowercase; the fix was to copy the exact ID instead of typing the display name. |
| 503 "high demand" errors from the chat model | Added retry with backoff (also for 429 rate limits) and kept the model configurable so a lighter model can be swapped in. |
| PDF text was polluted by page headers and footers and a table of contents page | Added a cleaning step that removes repeated lines and skips the contents page before chunking. |
| Same section numbers appear in different documents | Each chunk is prefixed with its source file name and section title before embedding. |
| Team skills are strongest in Python, but the brief requires a Node.js frontend | Moved the RAG pipeline to a Python FastAPI backend and kept Node.js as the frontend, so the logic and the requirement are both satisfied. |

## Learnings

- Retrieval quality decides answer quality, so retrieval was tested on its own (`search.py`) before connecting the LLM.
- Good chunk boundaries (by section) matter more than clever models for policy-style documents.
- Model names and availability change over time, so they belong in configuration, not in code.
- A strict "answer only from the context" prompt is the main defence against hallucination.
- Keeping secrets in `.env`, out of Git and out of the browser, is simple but essential.

## Cloud deployment (planned)

The app is prepared for deployment (a `start` script, the `PORT` variable, and a `BACKEND_URL` setting for the frontend). Deployment on Azure App Service is planned as a next step and is not completed yet.

## Possible improvements

- Deploy both services on Azure and set environment variables there.
- Add hybrid keyword + vector search and a re-ranking step.
- Build a small question set to measure retrieval accuracy automatically.
- Support streaming answers in the UI.
