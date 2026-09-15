# AgriLens

Evidence-grounded agricultural market intelligence from PDF reports. Each retrieval result retains its document name and page number; the Ollama prompt is restricted to those passages.

## Run

```bash
uv venv --python 3.12
uv pip install -r requirements.txt
cp .env.example .env
# Set OLLAMA_MODEL in .env after installing a model, for example: ollama pull qwen3:4b
uv run streamlit run app.py
```

Add up to five public, searchable reports to `data/reports/`, or upload them in the sidebar. Source landing pages are recorded in `data/sources.json`. Rebuild the index, then ask a question.

The app deliberately does not generate a summary when Ollama is unconfigured or unavailable; it exposes retrieved evidence instead. Scanned PDFs need OCR before they can be indexed.

The embedding model is intentionally loaded from the local Hugging Face cache at runtime. Download `all-MiniLM-L6-v2` once during environment setup (with network access), then the app will not make network requests to answer questions.
