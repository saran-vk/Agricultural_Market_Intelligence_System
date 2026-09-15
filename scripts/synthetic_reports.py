"""Generate realistic synthetic market reports as PDFs.

Used as a deterministic fallback when live downloads fail. Content is aligned
with the demo questions in the MVP plan (wheat 2022 spike, rice price drivers,
cotton production trend + year table, carryover stocks terminology, outlook).
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

WHEAT = [
    ("Global Wheat Market Report — 2023 Annual Review", "Page: 1"),
    (
        "Executive Summary",
        "Global wheat prices reached a record intra-year average of $438 per tonne "
        "in the second quarter of 2022, up 74 percent from the same period in 2021. "
        "The surge was driven by supply-side shocks, elevated input costs, and "
        "broad-based food inflation. Prices moderated from early 2023 as shipments "
        "recovered and the Black Sea corridor resumed.",
    ),
    (
        "Why did wheat prices spike in 2022?",
        "Three factors dominated the 2022 rally. First, the disruption of exports "
        "from the Black Sea region removed a substantial share of global milling wheat "
        "from world markets. Second, energy and fertilizer costs jumped, lifting "
        "production costs across exporting countries. Third, importers rushed to secure "
        "supplies, pushing inventories down. FAO's Cereal Supply and Demand Brief reported "
        "that global wheat stocks fell to their lowest level since 2016/17, which amplified "
        "price sensitivity to any further supply news.",
    ),
    (
        "Prices afterward",
        "From March 2023 the December milling wheat contract eased toward $270 per tonne "
        "as the corridor shipments stabilized. Comparatively high carryover stocks "
        "entering 2023/24 cushioned the market against renewed tightness, and successive "
        "large harvests in the southern hemisphere weighed on prices through the fourth "
        "quarter.",
    ),
    (
        "Terminology: Carryover stocks",
        "Carryover stocks refer to the quantity of a commodity that remains in storage "
        "from the previous marketing period and is available for use in the following period. "
        "They act as a buffer: higher carryover typically signals a more comfortable supply "
        "position and can dampen price volatility.",
    ),
    (
        "Outlook for the coming season",
        "The latest outlook indicates a modest global wheat surplus for 2023/24, with "
        "production expected to exceed use by roughly 9 million tonnes. Mild import demand "
        "and ample inventories point to a broadly stable price range, barring weather "
        "disruptions in the northern hemisphere growing season.",
    ),
]

RICE = [
    ("Global Rice Market Report — 2023 Review", "Page: 1"),
    (
        "Executive Summary",
        "International rice quotations averaged $625 per tonne in 2023, influenced above all "
        "by India's export restrictions, tightening inventories in major exporters, and firm "
        "demand from West Africa and the Middle East.",
    ),
    (
        "What factors influence rice prices?",
        "Rice prices are shaped by policy measures in exporting countries, notably export "
        "bans and minimum export prices; by monsoon outcomes in key growing regions; by "
        "government procurement programs; and by freight and energy costs. Currency movements "
        "against the US dollar also matter because most quotations are dollar-denominated. "
        "In 2023, the primary driver was the Indian export ban on non-basmati white rice, "
        "which redirected demand toward Thai and Vietnamese origins and lifted quotations "
        "across the board.",
    ),
    (
        "Traditional vs non-traditional exporters",
        "Thailand and Vietnam expanded shipments to fill the gap, while Cambodia and Pakistan "
        "gained market share. Import-dependent countries such as Indonesia and the "
        "Philippines restocked aggressively, sustaining upward pressure on prices through "
        "mid-2024 before harvests improved.",
    ),
    (
        "Terminology: Export ban",
        "An export ban is a government measure that restricts the volume of a commodity "
        "shipped abroad. Producers of the banning country typically benefit from lower "
        "domestic prices, while importing countries face higher world prices as supply tightens.",
    ),
]

COTTON = [
    ("Global Cotton Production Trends — 2019–2024", "Page: 1"),
    (
        "Overview",
        "World cotton production moved broadly sideways between 24 and 27 million tonnes "
        "over 2019–2024, with weather and area shifts driving year-to-year movements. "
        "Production recovered strongly in 2023/24 following drought-reduced harvests.",
    ),
    (
        "Production by marketing year",
        (
            "2019/20: 26.1 million tonnes\n"
            "2020/21: 24.4 million tonnes\n"
            "2021/22: 26.0 million tonnes\n"
            "2022/23: 24.7 million tonnes\n"
            "2023/24: 27.1 million tonnes\n"
            "2024/25 (f): 26.3 million tonnes"
        ),
    ),
    (
        "Commentary on the historical trend",
        "The overall trend over the 2019-2024 period was roughly flat, with a cyclical "
        "pattern driven by planted area responses to price signals and by monsoon and "
        "irrigation conditions in China, India, and the United States. Brazilian output "
        "rose steadily and reached a record share of global production by 2024.",
    ),
]

OUTLOOK = [
    ("Agricultural Commodity Outlook — 2024", "Page: 1"),
    (
        "Headline outlook",
        "The 2024 outlook points to easing global food prices relative to the 2022 peak, "
        "tempered by tighter supplies of rice and soft commodities. Wheat fundamentals are "
        "balanced, maize supplies remain ample, and weather risk in the southern hemisphere "
        "is the principal upside risk to prices.",
    ),
    (
        "Demand and stocks",
        "Global import demand is expected to normalize after two years of precautionary "
        "stocking. Ending stocks of major grains are projected to recover to comfortable "
        "levels, which should keep price movements range-bound unless production "
        "disruptions materialize.",
    ),
    (
        "Risks",
        "Key risks include El Niño impacts on Asian and Australian crops, further "
        "restrictions on exports from major suppliers, and elevated energy input costs. "
        "Downside risks to demand include a slower-than-expected recovery in emerging "
        "economies.",
    ),
]

STATS = [
    ("Commodity Statistical Review — 2024 Edition", "Page: 1"),
    (
        "Scope",
        "This annual review compiles key supply, demand, price, and trade statistics for "
        "major agricultural commodities, drawing on national and international sources.",
    ),
    (
        "Wheat — Key balances",
        (
            "Production 2022/23: 781 million tonnes\n"
            "Consumption 2022/23: 792 million tonnes\n"
            "Ending stocks 2022/23: 263 million tonnes\n"
            "Average export price 2022: $438/t\n"
            "Average export price 2023: $305/t"
        ),
    ),
    (
        "Cotton — Trade and prices",
        (
            "World trade 2023/24: 8.7 million tonnes\n"
            "Cotlook A index average 2023: 97.5 US cents/lb\n"
            "Cotlook A index average 2024: 90.2 US cents/lb"
        ),
    ),
    (
        "Note on data coverage",
        "All figures are rounded estimates. Prices are annual averages of international "
        "benchmarks and may differ from national farm-gate prices.",
    ),
]

STYLES = getSampleStyleSheet()
H1 = ParagraphStyle("H1X", parent=STYLES["Title"], fontSize=16, spaceAfter=14)
H2 = ParagraphStyle("H2X", parent=STYLES["Heading2"], fontSize=12.5, spaceBefore=12, spaceAfter=4)
BODY = ParagraphStyle("BodyX", parent=STYLES["BodyText"], fontSize=10, leading=14, spaceAfter=6)
META = ParagraphStyle("MetaX", parent=STYLES["Italic"], fontSize=9, leading=12)
PRE = ParagraphStyle("PreX", parent=STYLES["Code"], fontSize=9, leading=13)

_SPECS = [
    ("wheat", "Wheat Market Report", WHEAT),
    ("rice", "Rice Market Report", RICE),
    ("cotton", "Cotton Production Report", COTTON),
    ("outlook", "Commodity Outlook 2024", OUTLOOK),
    ("stats", "Commodity Statistical Review 2024", STATS),
]


def _build_pdf(path: Path, header: str, page_note: str, sections: list[tuple[str, str]]) -> None:
    doc = SimpleDocTemplate(str(path), pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm)
    story: list = [Paragraph(header, H1), Paragraph(page_note, META), Spacer(1, 8)]
    for title, body in sections:
        story.append(Paragraph(title, H2))
        if "\n" in body and body.count("\n") > 1:
            story.append(Paragraph(body.replace("\n", "<br/>"), PRE))
        else:
            story.append(Paragraph(body, BODY))
        story.append(Spacer(1, 4))
    if "Production by marketing year" in [t for t, _ in sections]:
        rows = [
            ["Marketing year", "World production (mn t)"],
            ["2019/20", "26.1"],
            ["2020/21", "24.4"],
            ["2021/22", "26.0"],
            ["2022/23", "24.7"],
            ["2023/24", "27.1"],
            ["2024/25 (f)", "26.3"],
        ]
        table = Table(rows, colWidths=[5 * cm, 7 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.append(Spacer(1, 6))
        story.append(table)
    doc.build(story)


def generate(count: int, data_dir: Path) -> int:
    made = 0
    for name, plain_header, sections in _SPECS[:count]:
        path = data_dir / f"{name}.pdf"
        if path.exists():
            print(f"    (skip existing {path.name})")
            continue
        _build_pdf(path, plain_header, f"{plain_header} — Sample edition", sections)
        made += 1
        print(f"    generated {path.name}")
    return made