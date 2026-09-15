# AgriLens — 3-Hour MVP Prototype Plan

## 1. MVP Objective

Build an **evidence-grounded agricultural market intelligence system** that converts complex agricultural and commodity reports into concise, understandable insights while preserving supporting sources.

The prototype should allow a user to:

- Use a small collection of agricultural/commodity PDF reports.
- Ask questions about market conditions, terminology, trends, and historical observations.
- Retrieve relevant information from the reports.
- Generate a concise LLM-based explanation.
- Show the supporting document and page number for the answer.

---

## 2. Core MVP Workflow

```text
Agricultural / Commodity PDFs
            ↓
      PDF Text Extraction
            ↓
        Text Chunking
            ↓
       Embeddings + FAISS
            ↓
        User Question
            ↓
   Semantic Retrieval (Top-K)
            ↓
       Relevant Evidence
            ↓
             LLM
            ↓
   Answer + Trend + Explanation
            ↓
      Source / Page Citations
```

---

## 3. MVP Features

### 3.1 Document Collection

Use a small, fixed set of **3–5 agricultural or commodity reports** for the prototype.

Recommended examples:

- Wheat market report
- Rice market report
- Cotton market report
- Agricultural commodity outlook report
- Government agricultural statistics report

Each extracted chunk should retain:

- Document name
- Page number
- Text content

### 3.2 Retrieval

Use semantic search to identify the most relevant sections of the reports.

**Implementation:**

- Sentence Transformers for embeddings
- FAISS for vector similarity search
- Retrieve the top 5 relevant chunks for each query

### 3.3 LLM Analysis

The LLM should generate answers using **only the retrieved report content**.

The response should cover, where applicable:

1. Direct answer
2. Market trend
3. Historical observation
4. Explanation of technical terminology
5. Supporting sources

### 3.4 Source Traceability

Every important answer should reference its source using:

```text
Document Name — Page Number
```

The system should avoid unsupported claims and should not invent facts, prices, or historical values.

### 3.5 Historical Trend View

Add a simple trend visualization when the retrieved reports contain usable historical numeric data.

Example:

```text
2020 ── Value
2021 ── Value
2022 ── Value
2023 ── Value
2024 ── Value
2025 ── Value
```

If suitable numeric data is not available, show a text-based historical observation instead of fabricating values.

---

## 4. Technology Stack

| Component | Technology |
|---|---|
| Language | Python |
| PDF extraction | PyMuPDF |
| Embeddings | Sentence Transformers |
| Vector search | FAISS |
| LLM | Any available LLM API |
| UI | Streamlit |
| Visualization | Plotly (optional) |

---

## 5. Suggested Project Structure

```text
project/
│
├── app.py
├── rag.py
├── requirements.txt
└── data/
    ├── wheat.pdf
    ├── rice.pdf
    └── cotton.pdf
```

### Responsibilities

**`app.py`**
- Streamlit interface
- User question input
- Display answer, trends, and sources

**`rag.py`**
- PDF extraction
- Chunking
- Embedding generation
- FAISS indexing
- Retrieval
- LLM prompt construction

**`data/`**
- Input agricultural and commodity reports

---

## 6. LLM Prompt Requirements

Use a prompt similar to:

```text
You are an agricultural market analyst.

Answer the user's question using ONLY the provided report excerpts.

Explain technical terminology in simple language.

Identify, when supported by the evidence:
1. Direct answer
2. Market trend
3. Historical observation
4. Important commodity information

Do not invent information.

For important claims, cite the document name and page number.

User Question:
{question}

Retrieved Evidence:
{context}
```

---

## 7. User Interface

The Streamlit interface should contain:

### Header

**AgriLens**  
*Agricultural Market Intelligence*

### Document Section

Show the reports available to the system.

### Question Section

```text
Ask about agricultural markets
[                                      ]

[ Analyze ]
```

### Results Section

Display:

- **Insight** — concise answer
- **Market Trend** — major movement or pattern
- **Historical Observation** — relevant historical information
- **Terminology** — simple explanation of technical terms
- **Sources** — document name and page number

---

## 8. 3-Hour Implementation Timeline

### 0:00–0:25 — Prepare Data

- Collect 3–5 suitable PDF reports.
- Place them in the `data/` folder.
- Confirm that the reports contain searchable text.

### 0:25–0:55 — PDF Processing

Implement:

```text
PDF → Pages → Text → Chunks → Metadata
```

Preserve document name and page number for every chunk.

### 0:55–1:25 — Retrieval

Implement:

```text
Chunks → Embeddings → FAISS → Top-K Retrieval
```

Verify that user questions return relevant report sections.

### 1:25–2:00 — LLM Integration

- Connect the LLM API.
- Pass retrieved evidence to the model.
- Enforce source-grounded responses.
- Test several representative queries.

### 2:00–2:35 — Streamlit UI

Implement:

- Document list
- Question input
- Analyze button
- Answer section
- Trend/observation section
- Sources section

### 2:35–2:50 — Trend Visualization

- Add a simple Plotly chart when structured historical data is available.
- Otherwise display a textual historical observation.

### 2:50–3:00 — Final Testing

Test the complete flow with prepared questions and confirm that every answer has supporting source references.

---

## 9. Demo Questions

Prepare questions that are directly answerable from the selected reports.

1. **Why did wheat prices increase during 2022?**
2. **What factors influence rice prices?**
3. **What has been the historical cotton production trend?**
4. **What does “carryover stock” mean?**
5. **What does the latest wheat outlook indicate?**

---

## 10. Expected MVP Output

For a question such as:

> Why did wheat prices increase during 2022, and what happened afterward?

The system should return a response similar to:

```text
INSIGHT
Wheat prices increased sharply during 2022 due to factors
identified in the retrieved market reports.

HISTORICAL OBSERVATION
Prices moderated afterward as market conditions changed.

TERMINOLOGY
Carryover stocks refers to the quantity of a commodity
remaining from the previous marketing period.

SOURCES
- Wheat Market Outlook — p. 14
- Global Commodity Review — p. 28
```

The exact explanation must be generated from the retrieved evidence rather than hard-coded.

---

## 11. MVP Success Criteria

The prototype is complete when it can:

- Load agricultural/commodity PDF reports.
- Extract and preserve page-level text.
- Retrieve relevant evidence for a user query.
- Generate an understandable answer using an LLM.
- Explain market terminology when supported by the reports.
- Summarize market trends and historical observations.
- Provide document and page references for supporting evidence.
- Run end-to-end through a simple Streamlit interface.

---

## 12. Scope for the 3-Hour Prototype

### Build Now

- PDF-based document collection
- Text extraction
- Chunking
- Embeddings
- FAISS retrieval
- LLM summarization
- Source/page citations
- Streamlit UI
- Basic historical trend visualization

### Defer

- Real-time commodity APIs
- Large-scale web scraping
- User authentication
- Complex databases
- Multi-agent workflows
- Fine-tuning
- Mobile application
- Production deployment infrastructure

---

## 13. One-Line Project Description

> **AgriLens is an evidence-grounded RAG system that transforms complex agricultural and commodity reports into simple market insights, trends, terminology explanations, and historical observations with traceable source references.**
