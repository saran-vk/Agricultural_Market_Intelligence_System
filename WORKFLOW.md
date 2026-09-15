# AgriLens — Codebase Workflow

End-to-end flow of `Agri_Market_Intel`: how the RAG pipeline starts, indexes reports, answers questions, and renders results.

---

## 1. Architecture Overview

Two modules, one entry point:

```
Agri_Market_Intel/
├── app.py        # Streamlit UI — frontend, state, rendering
├── rag.py        # RAG backend — PDF → chunks → embeddings → retrieval → LLM
├── .env          # Model config (OLLAMA_MODEL, OLLAMA_BASE_URL, EMBEDDING_MODEL)
├── .streamlit/config.toml   # Light theme
├── data/
│   ├── reports/  # Bundled corpora (tracked via .gitkeep)
│   ├── uploads/  # User-uploaded PDFs (gitignored)
│   └── index/    # Generated: chunks.json + reports.faiss (gitignored)
└── requirements.txt
```

- `app.py` imports from `rag.py` (`REPORTS_DIR`, `UPLOADS_DIR`, `ReportIndex`, `analyze`).
- All persistence lives under `data/`. Everything there is generated/derived or user-provided; nothing is central DB.

---

## 2. Startup Sequence (`app.py`)

Every Streamlit rerun re-executes the script top-to-bottom:

1. **Set page config** — `streamlit` config, `layout="wide"`, `initial_sidebar_state="collapsed"` (app.py:15).
2. **Inject CSS** — custom light theme styling, hides sidebar + chrome (app.py:22).
3. **Define helpers** — `get_index()` (cached), `corpus()`, `choose_question()`, `run_analysis_flow()`, `render_evidence_cards()`, `render_finding_card()`.
4. **Initialize session state** — `query`, `evidence`, `result`, `recent_questions`, `run_pending`, `analyzed_at` (app.py:355).
5. **Load the index** — `index = get_index()` → `ReportIndex.load()` reads `data/index/chunks.json` + `reports.faiss` (cached in memory).
6. **Derive stats** — `documents`, `pages`, `commodities` from loaded chunks; check `OLLAMA_MODEL` for "Local AI ready" status.
7. **Render UI** → topbar → hero → search panel → report library → run flow → metrics → findings → evidence.

---

## 3. Index-Build Workflow (only when needed)

Triggered by the **"Rebuild report index"** button in the Report library panel.

```
Upload (or drop PDFs in data/)          app.py UI
        │
        ▼
corpus() = reports/*.pdf + uploads/*.pdf
        │
        ▼
ReportIndex.build(pdfs)                 rag.py:75
        │
        ├─ per PDF: extract_pdf()        rag.py:49
        │     │  PyMuPDF open
        │     │  per page: get_text("text")
        │     │  _chunks(): 900-char window, sentence-boundary, 160 overlap
        │     │  skip if < 80 chars; record blank pages
        │     └─ Chunk(id, document_name, document_path, page_number, text, source_url)
        │
        ├─ model.encode(chunks)          sentence-transformers all-MiniLM-L6-v2 (local, CPU)
        │     └─ float32, L2-normalized
        │
        ├─ faiss.IndexFlatIP             inner-product ≈ cosine (normalized vectors)
        │
        ├─ write data/index/chunks.json  (chunk metadata)
        ├─ write data/index/reports.faiss (vectors)
        └─ returns {documents, chunks, unreadable_pages}
```

On success the UI shows `"{chunks} sections indexed"`; blank pages trigger a warning.

---

## 4. Query Workflow (the core loop)

Triggered when **✦ Analyze** is clicked or a suggestion chip sets `run_pending`.

```
Question typed                        app.py "query" text box
        │
        ▼
run_analysis_flow(index)              app.py:303
        │  st.spinner("preparing the market brief…")
        │
        ├─ index.retrieve(query)       rag.py:88   ← RETRIEVAL
        │     ├─ if no index → []
        │     ├─ embed the question (same MiniLM model)
        │     ├─ faiss index.search(question_vector, top_k=5)
        │     └─ returns top-5 Chunks (dedup'd, valid positions)
        │
        ├─ analyze(query, chunks)      rag.py:95   ← GENERATION
        │     ├─ no chunks → message "No relevant evidence is indexed yet."
        │     ├─ no OLLAMA_MODEL → message "Set OLLAMA_MODEL …" (evidence-first mode)
        │     ├─ build context: [S1] Doc — p.N \n <text> for each chunk
        │     ├─ prompt: "Use ONLY the evidence below… return JSON with
        │     │          insight / market_trend / historical_observation / terminology,
        │     │          each {text, citations:[S1..S5]}"
        │     ├─ POST /api/chat  (httpx → Ollama, format=json, timeout=90s)
        │     ├─ on HTTP error/parse error → graceful message
        │     └─ map S-labels back to Chunks → sections[key] = {text, sources}
        │
        ├─ store in session_state: evidence, result, analyzed_at
        └─ append question to recent_questions (max 5)
```

---

## 5. LLM Prompt Contract

The prompt (rag.py:101) asks Ollama for **strict JSON**:

```json
{
  "insight": { "text": "...", "citations": ["S1"] },
  "market_trend": { "text": "...", "citations": ["S1"] },
  "historical_observation": { "text": "...", "citations": ["S1"] },
  "terminology": { "text": "...", "citations": ["S1"] }
}
```

Hard rules enforced in the prompt:
- Use ONLY the provided evidence — no invented facts/prices/dates/definitions.
- Unsupported sections must literally say `Not established by the retrieved evidence.`
- `citations` array references labels `S1..S5` present in the context.

Backend parses citations back into real `Chunk` objects; the UI renders them.

---

## 6. Rendering Workflow

After analysis, `session_state` holds:

| Key | Type | Content |
|---|---|---|
| `evidence` | `list[Chunk]` | top-5 retrieved passages |
| `result` | `dict` | `{message, sections: {insight, market_trend, historical_observation, terminology: {text, sources}}}`, `sources` |
| `recent_questions` | `list[dict]` | `{question, asked_at}` history |

UI sections top-to-bottom:

1. **Topbar** — breadcrumb + status pill (`N reports indexed · Local AI ready / Evidence-first mode`).
2. **Hero** — static headline.
3. **Search panel** — text input + Analyze button + 4 suggestion chips.
4. **Report library** (expander) — upload, rebuild, list reports.
5. **Any message from `result.message`** — shown via `st.info`.
6. **Metric cards** — Reports / Pages / Sections / Commodities (derived from loaded chunks).
7. **Key findings** — 3 finding cards (`Market Trend`, `Historical Observation`, `Market Insight`) filled from `result["sections"]`.
8. **Supporting evidence** — evidence cards with `Document — p. N` citations + first 220-char excerpt; `View source` link if `source_url` set.

---

## 7. Configuration

Loaded once at module import (`.env` via `python-dotenv`):

| Variable | Default | Used by |
|---|---|---|
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | `ReportIndex` (`sentence_transformers`, `local_files_only=True`) |
| `OLLAMA_MODEL` | *(empty)* | `analyze()` — empty ⇒ evidence-first mode |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | `analyze()` — `/api/chat` POST |

Paths (`rag.py:21`):
- `REPORTS_DIR = data/reports`
- `UPLOADS_DIR  = data/uploads`
- `INDEX_DIR    = data/index`
- `METADATA_FILE = data/index/chunks.json`
- `FAISS_FILE    = data/index/reports.faiss`

---

## 8. State & Caching Rules

- `ReportIndex` is created once per process via `@st.cache_resource` — the FAISS index and model stay in memory across reruns.
- `model.encode(..., local_files_only=True)` — no network; the model must be in the local HuggingFace cache.
- Retrieval is deterministic: same query + same index ⇒ same top-k.
- `session_state` only persists within a browser session.

---

## 9. Failure Behaviors

| Failure | Where | Behavior |
|---|---|---|
| No index built | `retrieve()` | returns `[]` |
| No searchable text in PDFs | `build()` | raises `ValueError` → `st.error` |
| Ollama model not set | `analyze()` | message: "Set OLLAMA_MODEL …", evidence still shown |
| Ollama down / timeout / bad JSON | `analyze()` | safe `except` → "Ollama analysis is unavailable: …", evidence still shown |
| Blank query | `run_analysis_flow()` | `st.warning("Enter a question first.")` |
| Empty evidence | UI | "Run an analysis to view supporting passages…" placeholder |

---

## 10. Data Flow Diagram (ASCII)

```
 data/reports + data/uploads (PDFs)
        │
        ▼
 [Build] ──► extract_pdf ──► _chunks ──► Chunk[] ──► encode ──► FAISS + chunks.json
                                                                        │
   User query ────────────────────────────────────────────────────────►│
        │                                                              ▼
        └────► retrieve(query) ──► top-5 Chunks ──► analyze() ──► Ollama JSON
                                                              │
             UI: metrics ◄── stats ◄── loaded index           ▼
             UI: findings + evidence ◄── result["sections"] + sources
```

---

## 11. Local Run

```bash
cd Agri_Market_Intel
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
ollama pull <your-chat-model>      # optional; sets OLLAMA_MODEL=<model>
cp .env.example .env               # edit OLLAMA_MODEL / OLLAMA_BASE_URL

streamlit run app.py --server.port 8501
```