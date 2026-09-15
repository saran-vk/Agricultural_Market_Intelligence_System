# Agri Market Intelligence System — Build Plan

**Goal:** Ingest agricultural + commodity market reports, store them, retrieve relevant passages via hybrid search, and use an LLM to convert them into plain-language insights (trends, terminology, commodity info, historical observations) — with every claim linked back to its source.

- **Project:** Agri_Market_Intel
- **Mode:** Greenfield (empty repo)
- **System:** Linux, Python 3.14 + uv, Node 26, Docker 29, local Ollama, 14GB RAM / 16 cores

## 1. High-level architecture

```
┌─ ACQUISITION ──────────────────────────────────────────────┐
│  Scheduled fetch (USDA/FAO/AMIS/exchanges)   ▲ RSS poller  │
│  Web upload (PDF/DOCX/XLSX/TXT, OCR fallback)│  Source Mgr │
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ INGESTION ── normalize → metadata extract → chunk → table │
│               extraction → plain text + fingerprint (dedupe)│
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ STORAGE ──── Postgres + pgvector ─────────────────────────┐
│  reports │ chunks │ embeddings │ price series │ glossary ──┤
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ RETRIEVAL — hybrid: BM25 (full-text) ⊕ dense (pgvector) ──┤
│           RRF fusion + metadata filters (commodity/region)  │
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ LLM LAYER (hybrid) ── router ─────────────────────────────┐
│  Q&A/RAG │ term glossary │ trend summarizer │ history comp │
└───────────────┬─────────────────────────────────────────────┘
                ▼
┌─ APP — FastAPI + background workers (digests) ─────────────┐
└──────────────────┬──────────────────────────────────────────┘
                   ▼
         Web UI (Next.js): Chat w/ sources │ Upload │ Digests │ Source manager │ Glossary
```

## 2. The acquisition problem

Commodity/agri reports are scattered: few stable APIs, mostly HTML/PDF pages that change layout. Solution = **curated source registry + adapter pattern**, not a universal scraper.

### Design

- **Source Registry** (DB table): each entry = `{agency, report_name, url template, format, cadence, parser adapter, active}`. Admins curate/maintain it from the web UI.
- **Adapter per source** implementing 4 methods — the core abstraction:
  - `fetch()` — download report (PDF/HTML/XLSX)
  - `parse()` — extract structured text/tables (PDF → pdfplumber; HTML → html2text; XLSX → openpyxl)
  - `fingerprint()` — content hash for **dedupe + change detection** (reports get revised/corrected — needs versioning)
  - `cron()` — schedule (e.g., USDA weekly Friday, FAO monthly)
- **Tiered coverage:**
  1. **Priority connectors** (hand-built, tested): USDA AMS Market News, USDA/NASS, FAO GIEWS + AMIS bulletins, major exchange (CME/ICE) daily bulletins.
  2. **Generic RSS poller** — covers news agencies, USDA alerts, FAO feeds with near-zero per-source code (one generic adapter driven by feed config).
  3. **Web upload** — everything else via drag-drop, with **OCR fallback** (Tesseract via `pytesseract`) for scanned PDFs and **table extraction** (pdfplumber), since commodity data lives in tables.
  4. **Price series ingestion** (optional but high-value) — pull futures/spot series so "historical observations" compare report narrative vs. actual prices.
- **Reliability:** fingerprint dedupe, storage of raw originals alongside parsed text (auditability), per-source failure logging/retry, and a **Source Manager UI** to add/edit/disable sources without code changes.

**Result:** broad coverage with low per-source cost; the registry makes the system self-improving as more sources are discovered.

## 3. Storage (Postgres + pgvector)

- **Postgres (Docker) + `pgvector`** for: full-text search (BM25), dense embeddings, relational metadata. Rationale: single DB = one thing to run, transactions across reports/chunks, and Docker is already available.
- Core tables: `reports`, `report_versions`, `chunks` (with heading path), `embeddings` (vector), `sources` (registry), `price_series`, `glossary_terms`, `digests`, `citations`.
- Embeddings: local **sentence-transformers** (e.g. `bge-m3` or `nomic-embed-text` via Ollama) — no API cost, runs fine on 14GB RAM at ingest-time batch.

## 4. Retrieval (with citations)

- **Hybrid:** Postgres FTS (keyword) ⊕ pgvector (dense) → **Reciprocal Rank Fusion**.
- **Metadata filters:** commodity, region, agency, date range — critical so a 2015 report doesn't answer a 2026 question.
- **Citations are first-class:** every retrieved chunk carries `report_id`, `source_url`, `heading_path`, `page`. The LLM is instructed to emit citations; UI renders them as clickable links to the original doc/location. This is the "maintaining links to supporting sources" requirement.

## 5. LLM layer (hybrid)

- **Router:** local **Ollama** (e.g. Qwen2.5-7B/14B or Llama-3.1-8B) by default; cloud (OpenAI/Anthropic) auto-delegated for heavy/long digests when an API key is present.
- **Four capabilities** (matching the four requirements):
  1. **Q&A / RAG** — "What drove the wheat price spike in March?" with sourced answer + follow-ups.
  2. **Terminology explainer** — build a **glossary** automatically: NLP-extract unfamiliar terms from reports, LLM writes plain-language definitions stored in DB, surfaced inline (hover tooltip) in chat and digests.
  3. **Trend summarizer** — given a commodity + date window: direction, magnitude, drivers pulled from retrieved chunks, output with citations.
  4. **Historical observation comparator** — query top historical chunks + price series; explains "how does today compare to 2020?".

## 6. Application layer

- **Backend:** FastAPI. Endpoints for upload→ingest, hybrid search, chat stream (SSE), digests, sources CRUD, glossary. **APScheduler** workers: per-source cron fetches + scheduled digest generation (configurable: daily/weekly per commodity).
- **Web UI:** Next.js + Tailwind. Pages: **Chat** (streamed, inline citations), **Upload**, **Digests** (dashboard of auto-generated summaries), **Sources** (registry manager), **Glossary** (browse/search terms). Plain-language-first: headline insight + "Read the source →".

## 7. Build phases (with exit criteria)

| # | Phase | Deliverable | Done when |
|---|-------|-------------|-----------|
| 1 | **Foundations** | Repo, Docker compose (Postgres+pgvector), FastAPI skeleton, source registry schema, upload endpoint | Can upload a PDF → stored, fingerprinted, parsed |
| 2 | **Acquisition** | Adapter interface + priority connectors + RSS poller + OCR/table extraction | 3 real sources auto-fetch on schedule; dedupe works |
| 3 | **Retrieval** | Chunking (heading/table-aware) → embeddings → hybrid search + filters + citations | Query returns correct chunks with source links |
| 4 | **LLM layer** | Hybrid router, Q&A RAG, glossary pipeline, trend + history summarizers | Ask a financial-friend question → plain, cited answer |
| 5 | **Web app** | Chat + Upload + Sources + Glossary pages | End-to-end: upload → ask → sourced insight in browser |
| 6 | **Digests + polish** | Scheduled digests, evaluation set, tests, docs | Scheduled digest lands in dashboard with citations; eval harness > baseline |

## 8. Verification & eval strategy

- **Golden set:** ~30 Q&A pairs from real reports with known answers + expected citations; score answer correctness (LLM-judge) and **citation accuracy** (does the cited chunk actually support the claim).
- Unit tests per adapter (fixtures = saved sample reports), retrieval recall@k tests.
- Lint/type: `ruff` + `mypy` (Python), `eslint` + `tsc` (frontend); CI via GitHub Actions.

## 9. Open decisions

1. **DB**: Postgres+pgvector via Docker (recommended) vs. light sqlite-vec (zero-dependency but weaker FTS).
2. **Frontend**: Next.js (recommended, standard) vs. plain Vite+React SPA.
3. **Priority sources for Phase 2**: is USDA the primary focus, or a mix with FAO/AMIS? Narrows which connectors get built first.
4. **Price series**: include futures data ingestion in scope, or text-reports-only for now?

## 10. Recommended stack (once decisions are confirmed)

| Layer | Choice |
|-------|--------|
| Backend | Python 3.14 + FastAPI + SQLAlchemy/asyncpg + APScheduler |
| DB | Dockerized Postgres + pgvector |
| Embeddings | sentence-transformers (`bge-m3`) or Ollama `nomic-embed-text` |
| LLM | Ollama local default; OpenAI/Anthropic optional cloud |
| Parsing | pdfplumber (tables), html2text, openpyxl, pytesseract (OCR) |
| Frontend | Next.js + Tailwind + shadcn/ui |
| Eval/test | Golden set + LLM-judge + ruff/mypy + eslint/tsc + GitHub Actions |