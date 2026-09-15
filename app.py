"""Streamlit entry point for AgriLens."""

from __future__ import annotations

import shutil
from pathlib import Path

import plotly.express as px
import streamlit as st

from rag import REPORTS_DIR, UPLOADS_DIR, ReportIndex, analyze, find_year_values

st.set_page_config(page_title="AgriLens", page_icon="🌾", layout="wide")
st.title("AgriLens")
st.caption("Agricultural Market Intelligence — evidence-grounded answers from your reports")


@st.cache_resource
def get_index() -> ReportIndex:
    index = ReportIndex()
    index.load()
    return index


def corpus() -> list[Path]:
    return sorted(REPORTS_DIR.glob("*.pdf")) + sorted(UPLOADS_DIR.glob("*.pdf"))


def show_sources(sources: list) -> None:
    seen: set[str] = set()
    for source in sources:
        if source.id not in seen:
            seen.add(source.id)
            if source.source_url:
                st.markdown(f"- [{source.citation}]({source.source_url})")
            else:
                st.markdown(f"- {source.citation}")


with st.sidebar:
    st.header("Reports")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    uploaded = st.file_uploader("Add searchable PDF reports", type="pdf", accept_multiple_files=True)
    if uploaded:
        for file in uploaded:
            with (UPLOADS_DIR / Path(file.name).name).open("wb") as destination:
                shutil.copyfileobj(file, destination)
        st.success(f"Saved {len(uploaded)} report(s). Click Rebuild index.")
    documents = corpus()
    st.caption(f"{len(documents)} PDF(s) available")
    for document in documents:
        st.write(f"• {document.name}")
    if st.button("Rebuild index", type="primary", disabled=not documents):
        with st.spinner("Extracting report pages and creating the search index..."):
            try:
                result = get_index().build(documents)
                st.success(f"Indexed {result['chunks']} passages from {result['documents']} report(s).")
                if result["unreadable_pages"]:
                    st.warning("Some pages contained no readable text and may need OCR.")
            except Exception as error:
                st.error(f"Could not build the index: {error}")

question = st.text_input("Ask about agricultural markets", placeholder="What does the latest wheat outlook indicate?")
if st.button("Analyze", type="primary", disabled=not question.strip()):
    index = get_index()
    with st.spinner("Finding supporting evidence..."):
        evidence = index.retrieve(question)
    if not evidence:
        st.warning("No indexed evidence yet. Add searchable PDF reports and rebuild the index.")
    else:
        with st.spinner("Preparing grounded analysis..."):
            result = analyze(question, evidence)
        if result["message"]:
            st.info(result["message"])
        labels = {"insight": "Insight", "market_trend": "Market Trend", "historical_observation": "Historical Observation", "terminology": "Terminology"}
        for key, label in labels.items():
            st.subheader(label)
            section = result["sections"].get(key)
            if section:
                st.write(section["text"])
                show_sources(section["sources"])
            else:
                st.caption("Generated once Ollama is configured.")
        pairs = find_year_values(evidence)
        if pairs:
            st.subheader("Historical values found in evidence")
            st.plotly_chart(px.line(x=[item[0] for item in pairs], y=[item[1] for item in pairs], markers=True, labels={"x": "Year", "y": "Reported value"}), use_container_width=True)
        st.subheader("Retrieved evidence")
        for item in evidence:
            with st.expander(item.citation):
                st.write(item.text)
