# AMIS — Agricultural Market Intelligence & Retrieval System

A **Retrieval-Augmented Generation (RAG)** system that turns agricultural and commodity market PDF reports into plain-language, evidence-backed answers. Every claim is grounded in the retrieved report passages and linked back to its source document and page.

**Chat with your market reports.** Ask about price trends, supply/demand drivers, historical observations, or market terminology — AMIS retrieves the most relevant passages, summarizes them with a local LLM, and shows you exactly which report and page support each answer.

---

## ✨ Features

- 🔍 **Evidence-first Q&A** — free-form natural-language questions over your report corpus
- 📄 **RAG pipeline** — PDF ingestion → page-aware chunking → local embeddings → FAISS semantic search → LLM summarization
- 🗂️ **Page-level citations** — every answer traces to `Document — p. N`
- 🧠 **Structured analysis** — Insight, Market Trend, Historical Observation (Terminology generated in backend)
- 📊 **Key findings & supporting evidence cards** — skim conclusions, then verify the source excerpts
- 📚 **Report library** — upload PDFs in-app, rebuild the index on demand, list available reports
- 🏠 **Clean light-theme UI** — no sidebar; single-column dashboard flow
- 💻 **Fully local** — runs on CPU, no GPU required, no cloud API keys

---

## 🏗️ Architecture

```
Agri_Market_Intel/
├── app.py         # Streamlit UI — rendering, state, report library
├── rag.py         # RAG backend — extraction, chunking, embeddings, retrieval, LLM
├── WORKFLOW.md    # Detailed end-to-end codebase workflow
├── SRS.md         # Software Requirements Specification (v2, code-accurate)
├── .env.example   # Model configuration template
└── data/
    ├── reports/   # Bundled report corpus (PDFs)
    ├── uploads/   # User-uploaded PDFs
    └── index/     # Generated: chunks.json + reports.faiss
```

### Pipeline

```
PDF reports ──► extract text ──► chunk (900-char, overlap) ──► embed (all-MiniLM-L6-v2)
        ──► FAISS index (IndexFlatIP)
                                        ▲
        User question ─────────────────┘
        top-5 chunks ──► Ollama LLM (JSON) ──► Insight / Trend / Historical / Terminology
        ──► UI: metrics + finding cards + cited evidence
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (or `uv`)
- [Ollama](https://ollama.com/) installed and running (optional but recommended for LLM answers)

### 1. Setup

```bash
# With uv (recommended)
uv venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env

# Or with pip
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure the LLM (optional)

If Ollama is not configured, the app runs in **evidence-first mode** — it retrieves and shows the relevant passages without generating a summary.

```bash
ollama pull qwen3:4b            # any chat model works
# then edit .env:
#   OLLAMA_MODEL=qwen3:4b
#   OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Prepare the embedding model (one-time, with network)

The embedding model is loaded from the local Hugging Face cache and makes **no network calls at runtime**:

```bash
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
```

### 4. Run

```bash
streamlit run app.py
# or: uv run streamlit run app.py
```

Open the printed URL (default http://localhost:8501).

---

## 🧑‍🌾 How to Use

1. **Add reports** → open the **📚 Report library** expander, upload PDFs (or drop them in `data/reports/`).
2. **Rebuild the index** → click **Rebuild report index**.
3. **Ask a question** → type any natural-language question (or tap a suggestion chip), then **✦ Analyze**.
4. **Verify answers** → read the Key Findings cards; open **Supporting Evidence** to see the exact `Document — p. N` passages used.

### Example questions

- "What are the major price trends for wheat?"
- "Explain factors affecting cotton prices"
- "How did US maize production and exports change?"
- "Compare wheat prices across reports"
- "What does carryover stock mean?"

The model answers **only from the retrieved report passages** — questions outside your reports are answered with *"Not established by the retrieved evidence."*

---

## ⚙️ Configuration

| Variable | Default | Purpose |
|---|---|---|
| `OLLAMA_MODEL` | *(empty)* | Chat model for analysis; empty ⇒ evidence-first mode |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama server URL |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Local sentence-transformers model for retrieval |

Index artifacts (generated, gitignored):
- `data/index/chunks.json` — chunk metadata
- `data/index/reports.faiss` — embedding vectors

---

## 🧪 Reports That Work Well

Bundled corpus examples: WASDE outlooks, AMIS market monitors, FAO-style bulletins, and commodity price analyses. PDFs must contain **searchable text** (not scanned images) — scanned PDFs need OCR before indexing.

---

## 📚 Documentation

- `WORKFLOW.md` — full end-to-end codebase workflow (pipeline, prompt contract, failure behaviors, data-flow diagram)
- `SRS.md` — Software Requirements Specification (IEEE 830-style, traces every requirement to code)
- `AMIS_SRS.docx` — original SRS document

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit (`app.py`) |
| PDF parsing | PyMuPDF |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`) |
| Vector store | FAISS (CPU, `IndexFlatIP`) |
| LLM | Ollama (`/api/chat`), local |
| HTTP client | httpx |
| Config | python-dotenv (`.env`) |

---

## 👤 Author

**SARAN** — 7376242AD294
Department of Artificial Intelligence and Data Science, Bannari Amman Institute of Technology

---

## 📄 License

Academic / non-commercial use. Source documents are property of their respective publishers.