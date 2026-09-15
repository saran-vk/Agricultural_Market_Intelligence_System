"""Prepare the MVP report collection in data/.

Strategy:
  1. Try a set of well-known public commodity report PDF URLs.
  2. Verify each downloaded PDF has searchable text (PyMuPDF).
  3. Keep the ones that pass; if we end up with fewer than MIN_REPORTS,
     generate realistic synthetic reports so the demo always works.

Usage:
    python scripts/fetch_reports.py            # download + verify, synth fallback
    python scripts/fetch_reports.py --no-net   # synthetic only
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import httpx
import pymupdf  # PyMuPDF

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MIN_REPORTS = 3
MAX_PAGES = 200  # guard against giant downloads

# Probe order: earlier entries win. These are public, frequently-mirrored reports
# with relatively stable URLs. Any that fail or return non-text PDFs are skipped.
CANDIDATES = [
    {
        "name": "amis",
        "label": "AMIS Market Monitor",
        "urls": [
            "https://www.amis-outlook.org/fileadmin/user_upload/amis/docs/Market_monitor/AMIS_Market_Monitor_Current.pdf",
            "https://www.amis-outlook.org/fileadmin/user_upload/amis/docs/Market_monitor/AMIS_Market_Monitor_latest.pdf",
        ],
    },
    {
        "name": "fao_giews",
        "label": "FAO GIEWS Food Price Monitoring",
        "urls": [
            "https://openknowledge.fao.org/server/api/core/bitstreams/a19f65e2-1c3a-4d43-8afb-31d1a93a5e79/content",
        ],
    },
]


def _download(url: str, timeout: float = 30.0) -> bytes | None:
    try:
        with httpx.Client(follow_redirects=True, timeout=timeout) as client:
            resp = client.get(url)
            if resp.status_code == 200 and len(resp.content) > 4_000:
                return resp.content
    except Exception as exc:  # noqa: BLE001 - network probing is best-effort
        print(f"  ! probe failed: {exc}")
    return None


def _is_searchable_pdf(data: bytes) -> bool:
    try:
        doc = fitz.open(stream=data, filetype="pdf")
        n = min(doc.page_count, 5)
        text = "".join(doc[i].get_text() for i in range(n))
        doc.close()
        return len(text.strip()) > 200
    except Exception:
        return False


def _probe_candidates() -> dict[str, bytes]:
    """Return {label: pdf_bytes} for candidate URLs that pass the text check."""
    print("== Probing real report URLs ==")
    found: dict[str, bytes] = {}
    for cand in CANDIDATES:
        if cand["name"] in found:
            continue
        for url in cand["urls"]:
            print(f"- {cand['name']}: {url}")
            data = _download(url)
            if not data:
                continue
            # An HTML index page is not a report; force a text check.
            if not _is_searchable_pdf(data):
                print("  ! not a (searchable) PDF, skipping")
                continue
            found[cand["name"]] = data
            print(f"  OK -> {len(data)/1024:.0f} KB, searchable text")
            break
    return found


def write_pdf(name: str, label: str, data: bytes) -> Path:
    out = DATA_DIR / f"{name}.pdf"
    out.write_bytes(data)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-net", action="store_true", help="synthetic only")
    args = parser.parse_args()

    DATA_DIR.mkdir(exist_ok=True)

    real: dict[str, bytes] = {}
    if not args.no_net:
        real = _probe_candidates()
        print(f"== Real reports obtained: {len(real)} ==")

    for name, data in real.items():
        p = write_pdf(name, name, data)
        print(f"  wrote {p} ({len(data)/1024:.0f} KB, md5 {hashlib.md5(data).hexdigest()[:8]})")

    if len(real) >= MIN_REPORTS:
        print("== Enough real reports; no synthetic fallback needed ==")
        return 0

    print(f"== Only {len(real)} real report(s); generating synthetic fallback ==")
    from scripts import synthetic_reports  # noqa: PLC0415

    generated = synthetic_reports.generate(MIN_REPORTS - len(real), DATA_DIR)
    print(f"  generated {generated} synthetic report(s)")

    # Final verification pass across every PDF in data/
    print("== Final verification ==")
    ok = 0
    for pdf in sorted(DATA_DIR.glob("*.pdf")):
        try:
            doc = fitz.open(pdf)
            total_text = sum(len(doc[i].get_text()) for i in range(doc.page_count))
            doc.close()
            status = f"{pdf.name}: {total_text} chars of text"
            print("  " + status)
            if total_text > 500:
                ok += 1
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {pdf.name}: broken ({exc})")
    print(f"== {ok}/{len(list(DATA_DIR.glob('*.pdf')))} PDFs usable ==")
    return 0 if ok >= MIN_REPORTS else 1


if __name__ == "__main__":
    sys.exit(main())