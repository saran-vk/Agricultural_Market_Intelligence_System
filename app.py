"""AgriLens dashboard UI."""

from __future__ import annotations

import html
import os
import shutil
from datetime import datetime
from pathlib import Path

import streamlit as st

from rag import REPORTS_DIR, UPLOADS_DIR, ReportIndex, analyze

st.set_page_config(
    page_title="AgriLens | Market Intelligence",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

  :root {
    --green-950: #0f2e22;
    --green-900: #16402d;
    --green-800: #1a5238;
    --green-700: #08753f;
    --green-600: #1a6640;
    --green-500: #2d8a55;
    --green-100: #e7f8eb;
    --green-50: #f3fbf5;
    --gold-400: #d4a843;
    --gold-100: #faf3df;
    --surface: #ffffff;
    --surface-muted: #f7faf8;
    --border: #dce9df;
    --text: #123128;
    --text-muted: #5a7568;
    --shadow-sm: 0 2px 8px rgba(17, 65, 39, 0.06);
    --shadow-md: 0 8px 24px rgba(17, 65, 39, 0.08);
    --radius: 12px;
    --radius-lg: 16px;
  }

  html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, sans-serif; }
  .stApp { background: var(--surface-muted); color: var(--text); }
  #MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
  [data-testid="stSidebarCollapseButton"] { display: none !important; }
  [data-testid="stSidebar"][aria-expanded="false"] { display: none !important; }
  [data-testid="stSidebar"][aria-expanded="true"] { display: none !important; }
  section[data-testid="stSidebar"] { display: none !important; }
  .block-container { max-width: 1380px; padding: 1rem 1.5rem 2rem; }

  .topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.85rem;
  }
  .breadcrumb {
    color: var(--text-muted);
    font-size: 0.82rem;
  }
  .breadcrumb strong { color: var(--text); font-weight: 650; }
  .status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: var(--green-100);
    border: 1px solid #bde5c7;
    color: var(--green-700);
    padding: 0.38rem 0.75rem;
    border-radius: 999px;
    font-size: 0.76rem;
    font-weight: 700;
  }
  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #22c55e;
  }

  .hero {
    position: relative;
    overflow: hidden;
    border-radius: var(--radius-lg);
    padding: 1.75rem 1.85rem 1.35rem;
    margin-bottom: 1rem;
    border: 1px solid #c8dccf;
    background:
      linear-gradient(105deg, rgba(255, 255, 255, 0.92) 0%, rgba(255, 255, 255, 0.78) 42%, rgba(255, 255, 255, 0.55) 100%),
      linear-gradient(135deg, #e8f3c8 0%, #d4e8b8 35%, #f0dfa0 70%, #e8d090 100%);
    box-shadow: var(--shadow-md);
  }
  .hero::after {
    content: "";
    position: absolute;
    right: -2%;
    bottom: -18%;
    width: 42%;
    height: 120%;
    background: radial-gradient(circle, rgba(212, 168, 67, 0.25) 0%, transparent 70%);
    pointer-events: none;
  }
  .hero h1 {
    margin: 0 0 0.35rem;
    font-size: clamp(1.85rem, 2.8vw, 2.65rem);
    font-weight: 800;
    letter-spacing: -0.03em;
    color: var(--text);
    position: relative;
    z-index: 1;
  }
  .hero p {
    margin: 0 0 1.1rem;
    color: #3f6353;
    font-size: 0.98rem;
    max-width: 620px;
    position: relative;
    z-index: 1;
  }
  .search-panel {
    background: rgba(255, 255, 255, 0.96);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.85rem 0.95rem 0.75rem;
    margin: -0.35rem 0 1rem;
    box-shadow: var(--shadow-sm);
    position: relative;
    z-index: 2;
  }
  .search-panel .suggestions-label {
    color: var(--text-muted);
    font-size: 0.78rem;
    margin: 0.55rem 0 0.35rem;
  }

  .metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 1rem 1.05rem;
    min-height: 96px;
    box-shadow: var(--shadow-sm);
  }
  .metric-label {
    color: var(--text-muted);
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.35rem;
  }
  .metric-value {
    color: var(--text);
    font-size: 1.85rem;
    font-weight: 800;
    line-height: 1.2;
  }
  .metric-note {
    color: #7a9488;
    font-size: 0.74rem;
    margin-top: 0.2rem;
  }

  .panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    padding: 1.15rem 1.2rem;
    box-shadow: var(--shadow-sm);
  }
  .panel-title {
    color: var(--text);
    font-size: 1.02rem;
    font-weight: 800;
    margin: 0;
  }
  .panel-subtitle {
    color: var(--text-muted);
    font-size: 0.78rem;
    margin: 0.15rem 0 0.85rem;
  }

  .finding-card {
    background: #fcfffd;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.85rem 0.9rem;
    min-height: 118px;
    border-left: 4px solid var(--accent, var(--green-700));
    box-shadow: var(--shadow-sm);
  }
  .finding-title {
    font-size: 0.82rem;
    font-weight: 750;
    color: var(--text);
    margin-bottom: 0.35rem;
  }
  .finding-body {
    color: #48675a;
    font-size: 0.8rem;
    line-height: 1.5;
    margin: 0;
  }

  .evidence-card {
    background: #fcfffd;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 0.85rem;
    min-height: 150px;
    box-shadow: var(--shadow-sm);
  }
  .evidence-badge {
    display: inline-block;
    background: var(--green-100);
    color: var(--green-700);
    font-size: 0.66rem;
    font-weight: 700;
    padding: 0.18rem 0.45rem;
    border-radius: 999px;
    margin-bottom: 0.45rem;
  }
  .evidence-title {
    font-size: 0.82rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.35rem;
  }
  .evidence-text {
    font-size: 0.78rem;
    color: #5a7568;
    line-height: 1.45;
    margin: 0;
  }

  div[data-testid="column"] .stButton > button {
    border-radius: 10px;
    font-weight: 600;
    font-size: 0.78rem;
    border: 1px solid var(--border);
    background: #ffffff;
    color: #355b4d;
    min-height: 2.35rem;
  }
  div[data-testid="column"] .stButton > button:hover {
    border-color: #a8cdb7;
    color: var(--green-700);
    background: #f3fbf5;
  }
  .stTextInput input {
    border-radius: 10px !important;
    border: 1px solid #c9ddd0 !important;
    min-height: 2.85rem;
    font-size: 0.92rem;
    box-shadow: var(--shadow-sm);
  }
  .stButton > button[kind="primary"] {
    background: var(--green-700) !important;
    border-color: var(--green-700) !important;
    color: white !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    min-height: 2.85rem;
  }
  .stButton > button[kind="primary"]:hover {
    background: var(--green-600) !important;
    border-color: var(--green-600) !important;
  }

  @media (max-width: 900px) {
    .block-container { padding: 0.75rem; }
    .hero h1 { font-size: 1.75rem; }
  }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource
def get_index() -> ReportIndex:
    report_index = ReportIndex()
    report_index.load()
    return report_index


def corpus() -> list[Path]:
    return sorted(REPORTS_DIR.glob("*.pdf")) + sorted(UPLOADS_DIR.glob("*.pdf"))


def choose_question(question: str) -> None:
    st.session_state.query = question
    st.session_state.run_pending = True


def run_analysis_flow(index: ReportIndex) -> None:
    query = st.session_state.query.strip()
    if not query:
        st.warning("Enter a question first.")
        return
    with st.spinner("Retrieving evidence and preparing the market brief..."):
        st.session_state.evidence = index.retrieve(query)
        st.session_state.result = analyze(query, st.session_state.evidence)
        st.session_state.analyzed_at = datetime.now()
    if query not in st.session_state.recent_questions:
        st.session_state.recent_questions.insert(0, {"question": query, "asked_at": datetime.now()})
        st.session_state.recent_questions = st.session_state.recent_questions[:5]


def render_evidence_cards(evidence: list, limit: int = 3) -> None:
    if not evidence:
        st.markdown(
            "<p class='panel-subtitle'>Run an analysis to view supporting passages from your reports.</p>",
            unsafe_allow_html=True,
        )
        return
    columns = st.columns(min(limit, len(evidence)))
    for column, item in zip(columns, evidence[:limit]):
        with column:
            snippet = html.escape(item.text[:220] + ("…" if len(item.text) > 220 else ""))
            st.markdown(
                f"""
                <div class="evidence-card">
                  <span class="evidence-badge">Used for insights</span>
                  <div class="evidence-title">{html.escape(item.citation)}</div>
                  <p class="evidence-text">{snippet}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if item.source_url:
                st.link_button("View source", item.source_url, use_container_width=True)


def render_finding_card(title: str, text: str | None, accent: str, icon: str) -> None:
    body = html.escape(text or "Run an analysis to populate this section from indexed report evidence.")
    st.markdown(
        f"""
        <div class="finding-card" style="--accent:{accent};">
          <div class="finding-title">{icon} {title}</div>
          <p class="finding-body">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


for key, default in {
    "query": "",
    "evidence": [],
    "result": None,
    "recent_questions": [],
    "run_pending": False,
    "analyzed_at": None,
}.items():
    st.session_state.setdefault(key, default)


index = get_index()
loaded = index.load() if not index.chunks else True
chunks = index.chunks if loaded else []
documents = len({chunk.document_name for chunk in chunks})
pages = len({(chunk.document_name, chunk.page_number) for chunk in chunks})
commodities = [
    name
    for name in ("wheat", "rice", "cotton", "maize", "corn", "soy")
    if any(name in chunk.text.lower() for chunk in chunks)
]
ollama_ready = bool(os.getenv("OLLAMA_MODEL", "").strip())

st.markdown(
    f"""
    <div class="topbar">
      <div class="breadcrumb"><strong>Overview</strong> / Agricultural market intelligence</div>
      <span class="status-pill">
        <span class="status-dot"></span>
        {documents} report{"s" if documents != 1 else ""} indexed · {"Local AI ready" if ollama_ready else "Evidence-first mode"}
      </span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
      <h1>Understand the market. Faster.</h1>
      <p>Turn complex agricultural and commodity reports into clear, evidence-backed insights with AgriLens.</p>
    </div>
    <div class="search-panel">
    """,
    unsafe_allow_html=True,
)

search_col, action_col = st.columns([6.2, 1.2])
with search_col:
    st.text_input(
        "Ask about your reports",
        key="query",
        placeholder="What would you like to know about your reports?",
        label_visibility="collapsed",
    )
with action_col:
    run_clicked = st.button("✦ Analyze", type="primary", use_container_width=True)

st.markdown("<div class='suggestions-label'>Try asking:</div>", unsafe_allow_html=True)
suggestions = [
    "What are the major price trends?",
    "Explain factors affecting cotton prices",
    "What does carryover stock mean?",
    "Compare wheat prices across reports",
]
suggestion_columns = st.columns(4)
for column, suggestion in zip(suggestion_columns, suggestions):
    with column:
        st.button(suggestion, use_container_width=True, on_click=choose_question, args=(suggestion,))

st.markdown("</div></div>", unsafe_allow_html=True)

REPORTS_DIR.mkdir(parents=True, exist_ok=True)
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
docs = corpus()
with st.expander("📚 Report library", expanded=False):
    uploads = st.file_uploader(
        "Upload searchable PDF reports",
        type="pdf",
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
    if uploads:
        for upload in uploads:
            with (UPLOADS_DIR / Path(upload.name).name).open("wb") as destination:
                shutil.copyfileobj(upload, destination)
        st.success(f"Added {len(uploads)} report(s).")
        docs = corpus()
    library_col, _ = st.columns([1.2, 3])
    with library_col:
        if st.button("Rebuild report index", type="primary", use_container_width=True, disabled=not docs):
            with st.spinner("Indexing reports..."):
                try:
                    built = get_index().build(docs)
                    st.success(f"{built['chunks']} sections indexed.")
                    if built["unreadable_pages"]:
                        st.warning("Some pages have no searchable text.")
                except Exception as error:
                    st.error(f"Indexing failed: {error}")
    st.caption(f"{len(docs)} report(s) available in library")
    if docs:
        with st.expander("View reports", expanded=False):
            for doc in docs:
                st.caption(f"• {doc.name}")

if run_clicked or st.session_state.run_pending:
    st.session_state.run_pending = False
    run_analysis_flow(index)

evidence = st.session_state.evidence
result = st.session_state.result
if result and result.get("message"):
    st.info(result["message"])

metric_columns = st.columns(4)
metric_data = [
    ("📚", "Total Reports", documents, "Agricultural & commodity reports"),
    ("📄", "Total Pages", pages, "Pages of searchable evidence"),
    ("⌕", "Searchable Sections", len(chunks), "Indexed for smart retrieval"),
    ("🌾", "Key Commodities", len(commodities), ", ".join(name.title() for name in commodities) or "Awaiting report evidence"),
]
for column, (icon, label, value, note) in zip(metric_columns, metric_data):
    with column:
        st.markdown(
            f"""
            <div class="metric-card">
              <div class="metric-label">{icon} {label}</div>
              <div class="metric-value">{value:,}</div>
              <div class="metric-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div class='panel-subtitle' style='margin-top:1rem;'>Key findings</div>", unsafe_allow_html=True)
finding_rows = [
    ("Market Trend", "market_trend", "#e07b39", "↗"),
    ("Historical Observation", "historical_observation", "#08753f", "◷"),
    ("Market Insight", "insight", "#3b82c4", "◆"),
]
finding_columns = st.columns(3)
for column, (title, key, accent, icon) in zip(finding_columns, finding_rows):
    with column:
        section_text = result["sections"].get(key, {}).get("text") if result else None
        render_finding_card(title, section_text, accent, icon)

st.markdown(
    """
    <div class="panel-subtitle" style="margin-top:1rem;">📎 Supporting Evidence</div>
    <div class="panel-subtitle">Passages used for the current analysis</div>
    """,
    unsafe_allow_html=True,
)
render_evidence_cards(evidence)
