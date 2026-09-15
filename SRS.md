# Software Requirements Specification

## AgriLens — Agricultural Market Intelligence & Retrieval System (AMIS)

**Version 1.0**
**Date: September 15, 2026**
**Prepared by: SARAN**
**Registration No: 7376242AD294**
**Department of Artificial Intelligence and Data Science, Bannari Amman Institute of Technology**

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [System Features (Functional Requirements)](#3-system-features-functional-requirements)
4. [External Interface Requirements](#4-external-interface-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [Data Requirements](#6-data-requirements)
7. [Appendix: Sample Query Flow](#7-appendix-sample-query-flow)
8. [Future Enhancements](#8-future-enhancements)

---

## 1. Introduction

### 1.1 Purpose
This document specifies the software requirements for **AgriLens (Agricultural Market Intelligence System, AMIS)**, a Retrieval-Augmented Generation (RAG) system that converts agricultural and commodity market PDF reports into plain-language, evidence-backed answers. Every generated claim is grounded in retrieved report excerpts and linked back to its source document and page. This SRS is intended for the developer, project guide/evaluator, and future contributors.

### 1.2 Scope
AMIS ingests agricultural and commodity market PDF reports, indexes them into a searchable semantic store, and answers natural-language user questions by retrieving the most relevant passages and summarizing them with a local LLM. The system:

- Accepts PDF reports via upload or a local `data/reports` directory and rebuilds the searchable index on demand.
- Extracts per-page text, detects unreadable (blank) pages, and splits content into overlapping, page-traceable chunks.
- Embeds chunks locally (no GPU) and stores them in a FAISS vector index.
- Retrieves the top-k most relevant chunks for a user query using semantic similarity.
- Generates a structured, evidence-constrained analysis with an LLM, organized into **Insight**, **Market Trend**, **Historical Observation**, and **Terminology** sections.
- Returns each claim with a citation to the originating document and page.
- Displays results through a Streamlit web interface, including key-finding cards, supporting evidence excerpts, and report-library management.

The system does **not** provide financial or trading advice, does not execute trades, and does not guarantee the accuracy of third-party source data — it summarizes and explains what is already published.

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|---|---|
| **RAG** | Retrieval-Augmented Generation — combining document retrieval with LLM generation |
| **LLM** | Large Language Model |
| **SRS** | Software Requirements Specification |
| **Chunk** | A segmented portion of a source document stored for retrieval |
| **Embedding** | A numeric vector representation of text used for semantic search |
| **FAISS** | Facebook AI Similarity Search — vector index used for retrieval |
| **WASDE** | World Agricultural Supply and Demand Estimates (USDA report) |
| **MSP** | Minimum Support Price |
| **Top-k** | The k most similar items returned by a retrieval search |

### 1.4 References
- IEEE Std 830-1998 — Recommended Practice for Software Requirements Specifications
- USDA World Agricultural Supply and Demand Estimates (WASDE) reports
- FAO Global Information and Early Warning System bulletins
- FAISS / sentence-transformers / PyMuPDF / Streamlit / Ollama documentation

### 1.5 Overview
Section 2 describes the product at a high level. Section 3 details functional requirements. Section 4 covers external interfaces. Section 5 defines non-functional requirements. Section 6 lists data requirements. Section 7 gives a sample query flow. Section 8 lists future enhancements.

---

## 2. Overall Description

### 2.1 Product Perspective
AMIS is a standalone, single-machine system composed of five pipelined stages: **ingestion**, **document processing**, **embedding and vector storage**, **retrieval with LLM summarization**, and **insight output with citations**. It is an explanation and retrieval layer on top of source publications, not a replacement for them.

### 2.2 Product Functions
- Ingest agricultural/commodity PDFs from a local `data/reports` directory or user uploads (`data/uploads`).
- Extract per-page text and identify pages with no searchable text (blank pages).
- Chunk extracted text into overlapping, sentence-boundary-aware segments, each carrying document name, page number, and a stable chunk ID.
- Generate local CPU-based embeddings and index chunks in a FAISS flat index for semantic search.
- Retrieve the top-k relevant chunks for a natural-language query.
- Generate evidence-grounded, structured LLM analyses (Insight, Market Trend, Historical Observation, Terminology).
- Return every claim with a citation to its document name and page.
- Present results via a Streamlit web interface with key findings, supporting evidence, metric summaries, and report-library management.

### 2.3 User Classes and Characteristics

| User Class | Characteristics |
|---|---|
| **Student / Researcher** | Wants plain-language summaries and terminology explanations of market reports |
| **Project Evaluator** | Reviews retrieval accuracy, citation correctness, and summarization quality |
| **Future Contributor** | Extends the system with new data sources or additional analysis modules |

### 2.4 Operating Environment
- **Backend:** Python 3.11+ ingestion and retrieval pipeline.
- **Frontend:** Streamlit web interface for querying and viewing results.
- **Embedding model:** `sentence-transformers` `all-MiniLM-L6-v2`, loaded locally with `local_files_only`.
- **Vector store:** FAISS flat index (inner-product on L2-normalized vectors).
- **Vector index files:** `data/index/chunks.json` (metadata) and `data/index/reports.faiss` (vectors).
- **LLM access:** Local Ollama server via REST API (`OLLAMA_BASE_URL`, default `http://localhost:11434`), model configured by `OLLAMA_MODEL`.
- **Deployment target:** local development environment / single-server hosting; no GPU required.

### 2.5 Design and Implementation Constraints
- The LLM must only generate claims grounded in retrieved chunks; unsupported or hallucinated figures are treated as defects.
- Embeddings and retrieval must run locally (CPU-friendly model, no GPU dependency).
- API keys and LLM configuration must come from environment variables via `.env` (`OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `EMBEDDING_MODEL`) — never hard-coded.
- Source documents are assumed to be publicly available and licensed for non-commercial academic use.
- No real-time trading or transactional functionality is in scope.

### 2.6 Assumptions and Dependencies
- Source reports are published in a text-extractable PDF format (not scanned images requiring OCR, unless added as a future enhancement).
- A local Ollama server with the configured chat model is available for LLM generation; if unavailable, the system degrades gracefully to evidence-only mode.
- The embedding model (`all-MiniLM-L6-v2`) is available in the local model cache.
- Users have basic familiarity with agricultural market terms or seek the system precisely to learn them.

---

## 3. System Features (Functional Requirements)

### 3.1 Document Ingestion Module

**Description:** Accepts agricultural and commodity market PDFs, persists them, and exposes the current report corpus for indexing.

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-1.1 | The system shall accept PDF reports uploaded through the web interface and store them in `data/uploads/`. | High | `app.py` — Report library expander, file uploader |
| FR-1.2 | The system shall treat all PDFs in `data/reports/` and `data/uploads/` as the active corpus. | High | `app.py:corpus()`, `rag.py:REPORTS_DIR/UPLOADS_DIR` |
| FR-1.3 | The system shall report blank/unreadable pages per document so the user can be warned during indexing. | High | `rag.py:extract_pdf()` returns `blank`; `app.py` warning |
| FR-1.4 | The system shall raise a clear error if no searchable text exists across the selected PDFs. | High | `rag.py:build()`, `raise ValueError(...)` |

### 3.2 Document Processing Module

**Description:** Parses PDFs into page-level text and splits them into semantically coherent, page-traceable chunks.

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-2.1 | The system shall extract text per page from PDFs using PyMuPDF. | High | `rag.py:extract_pdf()` |
| FR-2.2 | The system shall split page text into chunks using a configurable window (~900 characters) with sentence-boundary alignment and overlap (~160 characters). | High | `rag.py:_chunks()` |
| FR-2.3 | The system shall skip pages/segments with insufficient text (fewer than ~80 characters). | Medium | `rag.py:_chunks()` |
| FR-2.4 | Each chunk shall retain metadata: a stable ID (hash prefix + page + offset), document name, document path, and page number. | High | `rag.py:Chunk` dataclass, `extract_pdf()` |
| FR-2.5 | Each chunk shall expose a human-readable citation of the form `Document Name — p. N`. | High | `rag.py:Chunk.citation` |

### 3.3 Embedding and Vector Store Module

**Description:** Converts chunks into normalized embeddings and indexes them for semantic retrieval.

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-3.1 | The system shall generate L2-normalized embeddings for every chunk using the configured local embedding model. | High | `rag.py:ReportIndex.build()` |
| FR-3.2 | The system shall store chunk vectors in a FAISS inner-product index and chunk metadata in `data/index/chunks.json`. | High | `rag.py:build()` — `faiss.write_index`, `METADATA_FILE` |
| FR-3.3 | The system shall load an existing index at startup when persisted files are present. | High | `rag.py:ReportIndex.load()` |
| FR-3.4 | The system shall rebuild the full index on demand via the "Rebuild report index" action. | Medium | `rag.py:build()`, `app.py` button |

### 3.4 Retrieval and LLM Summarization Module

**Description:** Retrieves relevant chunks for a query and generates a structured, evidence-constrained analysis.

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-4.1 | The system shall return the top-k (default 5) most relevant chunks for a query via semantic similarity search. | High | `rag.py:retrieve()` |
| FR-4.2 | The system shall return an empty retrieval result for blank queries. | Medium | `rag.py:retrieve()` |
| FR-4.3 | The system shall generate a structured LLM analysis with sections: **insight**, **market_trend**, **historical_observation**, and **terminology**. | High | `rag.py:analyze()` |
| FR-4.4 | The system shall constrain the LLM to use ONLY the retrieved evidence and to mark unsupported sections as "Not established by the retrieved evidence." | High | `rag.py:analyze()` prompt |
| FR-4.5 | The system shall return a clear message instead of an LLM answer when no Ollama model is configured. | Medium | `rag.py:analyze()` — `if not model` |
| FR-4.6 | The system shall handle LLM/HTTP failures gracefully by returning an explanatory message rather than crashing. | High | `rag.py:analyze()` — `try/except httpx.HTTPError` |
| FR-4.7 | The system shall map each section's JSON citations (`S1`, `S2`, …) back to the corresponding retrieved chunks. | High | `rag.py:analyze()` — `labels` mapping |

### 3.5 Insight Output and Citation Module

**Description:** Presents the generated analysis alongside verifiable links to supporting source material.

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-5.1 | The system shall return every analysis section paired with its cited source chunks. | High | `rag.py:analyze()` — `sections[key]["sources"]` |
| FR-5.2 | The system shall display key-finding cards for Market Trend, Historical Observation, and Market Insight. | High | `app.py` — finding cards |
| FR-5.3 | The system shall display supporting evidence cards with the document citation and a text excerpt for each retrieved chunk. | High | `app.py:render_evidence_cards()` |
| FR-5.4 | The system shall show a "View source" link for a chunk when a source URL is present. | Medium | `app.py:render_evidence_cards()` |

### 3.6 User Interface Module

**Description:** A Streamlit-based interface for querying, viewing results, and managing the report library.

| ID | Requirement | Priority | Trace |
|---|---|---|---|
| FR-6.1 | The system shall provide a free-form text input for questions. | High | `app.py` — `st.text_input("query")` |
| FR-6.2 | The system shall provide clickable suggestion questions that populate the query box. | Medium | `app.py` — suggestion buttons |
| FR-6.3 | The system shall display summary metrics (reports, pages, sections, commodities). | Medium | `app.py` — metric cards |
| FR-6.4 | The system shall provide a collapsible "Report library" panel to upload PDFs, rebuild the index, and list available reports. | Medium | `app.py` — Report library expander |
| FR-6.5 | The interface shall have a light theme and hide the sidebar so it cannot be reopened once collapsed. | Low | `app.py` — `.streamlit/config.toml`, sidebar CSS |

---

## 4. External Interface Requirements

### 4.1 User Interfaces
- A web-based query interface (Streamlit) with a question input, suggestion chips, metric cards, key-finding cards, and supporting evidence cards.
- A collapsible report-library panel with PDF upload, "Rebuild report index", and a list of available reports.

### 4.2 Software Interfaces
- **PDF parsing:** PyMuPDF (`pymupdf`) for page text extraction.
- **Embeddings:** `sentence-transformers` with `all-MiniLM-L6-v2` (local, CPU).
- **Vector store:** FAISS (`faiss-cpu`) flat inner-product index.
- **LLM:** Local Ollama REST API (`/api/chat`) via `httpx`.
- **Configuration:** `.env` file loaded with `python-dotenv`.

### 4.3 Communication Interfaces
- HTTP calls to the local Ollama server (default `http://localhost:11434`).
- Local file access for document ingestion and index persistence (`data/reports`, `data/uploads`, `data/index`).

---

## 5. Non-Functional Requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-1 | Performance | Retrieval over an index of up to ~5,000 chunks shall complete in under ~2 seconds; LLM generation completes within the Ollama request timeout (90 s). |
| NFR-2 | Performance | Ingestion and indexing of a typical 20-page report shall complete within 60 seconds on a standard laptop CPU. |
| NFR-3 | Security | API/model configuration shall be loaded from environment variables or `.env`; no secrets hard-coded in source. |
| NFR-4 | Security | Ingested documents shall only be transmitted to the configured local Ollama LLM server. |
| NFR-5 | Reliability | LLM failures or timeouts shall produce a clear error message rather than a silent or incorrect answer. |
| NFR-6 | Reliability | Retrieval shall be deterministic: the same query against the same index returns the same top-k chunks. |
| NFR-7 | Portability | The system shall run on a standard development machine without GPUs. |
| NFR-8 | Maintainability | The ingestion, chunking, and retrieval stages shall be independently testable and replaceable (e.g., swapping FAISS or the embedding model). |
| NFR-9 | Usability | Generated analyses shall be understandable to users without a finance/economics background. |
| NFR-10 | Usability | Every displayed answer shall visibly indicate its source document(s) without extra navigation. |
| NFR-11 | Accuracy | Unsupported claims must be marked "Not established by the retrieved evidence" rather than asserted as fact. |

---

## 6. Data Requirements

### 6.1 Source Data
- **Format:** PDF reports (e.g., WASDE, FAO bulletins, commodity outlooks, AMIS market monitors).
- **Location:** `data/reports/` (bundled) and `data/uploads/` (user uploads).
- **Volume:** any number of reports; storage bound by disk.

### 6.2 Derived Data
- **Index metadata:** `data/index/chunks.json` — JSON array of chunk records (id, document_name, document_path, page_number, text, source_url).
- **Index vectors:** `data/index/reports.faiss` — FAISS binary index of normalized embeddings.

### 6.3 Data Handling Notes
- Duplicate PDF filenames across uploads are overwritten by the latest upload.
- Rebuilding the index rewrites both metadata and vector files atomically from the current corpus.

---

## 7. Appendix: Sample Query Flow

1. **User action:** Uploads a few commodity PDFs via the Report library panel and clicks **Rebuild report index**.
2. **System action:** Extracts per-page text, chunks it with metadata, embeds chunks with MiniLM, and writes `chunks.json` + `reports.faiss`.
3. **User action:** Types *"Why did wheat prices rise this quarter?"* or clicks a suggestion chip, then **Analyze**.
4. **System action:** Retrieves the top-5 most relevant chunks from the FAISS index.
5. **LLM action:** Generates a JSON analysis (Insight, Market Trend, Historical Observation, Terminology) using only the retrieved excerpts, each claim citing `S1..S5`.
6. **Presentation:** UI shows metrics, the three key-finding cards, and supporting evidence cards citing `Document — p. N`; a "View source" link appears when a source URL exists.

If the Ollama server is down, the UI shows *"Ollama analysis is unavailable: …"* and still lists the retrieved evidence. If a section is unsupported by evidence, it reads *"Not established by the retrieved evidence."*

---

## 8. Future Enhancements

Items considered out of scope for the current version, tracked for future iterations:

| ID | Enhancement | Notes |
|---|---|---|
| FE-1 | CSV and HTML ingestion | Currently PDF-only; add structured price-data pipeline |
| FE-2 | Source/commodity/date/document-type metadata tagging | Enables filtered retrieval |
| FE-3 | Retrieval filtering by commodity, date range, and source | Requires FE-2 metadata |
| FE-4 | Incremental indexing without full rebuild | Add new chunks to the existing store |
| FE-5 | Section-aware chunking | Replace fixed-window chunking with logical sections and preserve tables |
| FE-6 | Trend comparison across time periods | Retrieve and contrast chunks from different dates |
| FE-7 | Ingestion/chunking logging | For debugging traceability (NFR-8) |
| FE-8 | OCR support for scanned/image-based reports | |
| FE-9 | Multi-language support for regional market bulletins | |
| FE-10 | Automated scheduled ingestion | Cron-based instead of manual upload |
| FE-11 | Evaluation harness | Measure citation accuracy and hallucination rate |