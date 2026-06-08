"""
PDF Export Utility for AI Company Intelligence Reports
Uses ReportLab to convert markdown reports to styled PDFs.
"""

import os
import re
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# ── Colour palette ────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#0D1B2A")
SLATE     = colors.HexColor("#1B2A3B")
ACCENT    = colors.HexColor("#1565C0")
GOLD      = colors.HexColor("#F9A825")
LIGHT_BG  = colors.HexColor("#F0F4F8")
MID_GRAY  = colors.HexColor("#B0BEC5")
TEXT_DARK = colors.HexColor("#1A1A2E")
WHITE     = colors.white


def _styles():
    """Build a custom style sheet."""
    base = getSampleStyleSheet()

    custom = {
        "cover_title": ParagraphStyle(
            "cover_title",
            fontName="Helvetica-Bold",
            fontSize=26,
            textColor=WHITE,
            alignment=TA_CENTER,
            spaceAfter=8,
            leading=32,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub",
            fontName="Helvetica",
            fontSize=13,
            textColor=GOLD,
            alignment=TA_CENTER,
            spaceAfter=4,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta",
            fontName="Helvetica",
            fontSize=10,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=2,
        ),
        "h1": ParagraphStyle(
            "h1",
            fontName="Helvetica-Bold",
            fontSize=18,
            textColor=NAVY,
            spaceBefore=20,
            spaceAfter=8,
            borderPadding=(0, 0, 4, 0),
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Helvetica-Bold",
            fontSize=14,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "h3",
            fontName="Helvetica-BoldOblique",
            fontSize=12,
            textColor=SLATE,
            spaceBefore=10,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body",
            fontName="Helvetica",
            fontSize=10,
            textColor=TEXT_DARK,
            leading=15,
            spaceAfter=6,
            alignment=TA_JUSTIFY,
        ),
        "bullet": ParagraphStyle(
            "bullet",
            fontName="Helvetica",
            fontSize=10,
            textColor=TEXT_DARK,
            leading=14,
            spaceAfter=3,
            leftIndent=16,
            bulletIndent=0,
        ),
        "table_header": ParagraphStyle(
            "table_header",
            fontName="Helvetica-Bold",
            fontSize=9,
            textColor=WHITE,
            alignment=TA_CENTER,
        ),
        "table_cell": ParagraphStyle(
            "table_cell",
            fontName="Helvetica",
            fontSize=9,
            textColor=TEXT_DARK,
            leading=12,
        ),
        "blockquote": ParagraphStyle(
            "blockquote",
            fontName="Helvetica-Oblique",
            fontSize=10,
            textColor=SLATE,
            leading=14,
            leftIndent=20,
            spaceAfter=6,
            borderPadding=(6, 6, 6, 6),
        ),
        "source": ParagraphStyle(
            "source",
            fontName="Helvetica",
            fontSize=8,
            textColor=MID_GRAY,
            leading=11,
            spaceAfter=2,
        ),
        "confidence": ParagraphStyle(
            "confidence",
            fontName="Helvetica-Bold",
            fontSize=10,
            textColor=GOLD,
            spaceAfter=4,
        ),
    }
    return custom


def _clean(text: str) -> str:
    """Strip markdown syntax that ReportLab can't handle natively."""
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*",   r"<i>\1</i>",  text)
    text = re.sub(r"`(.*?)`",     r"<font face='Courier'>\1</font>", text)
    # Escape bare ampersands that break XML parsing
    text = re.sub(r"&(?!amp;|lt;|gt;|nbsp;|quot;)", "&amp;", text)
    return text


def _confidence_color(score_text: str) -> colors.Color:
    """Return a traffic-light color based on X/10 score."""
    m = re.search(r"(\d+)/10", score_text)
    if not m:
        return MID_GRAY
    score = int(m.group(1))
    if score >= 8:
        return colors.HexColor("#2E7D32")   # green
    if score >= 5:
        return colors.HexColor("#F57F17")   # amber
    return colors.HexColor("#C62828")       # red


def markdown_to_pdf(markdown_text: str, company_name: str) -> bytes:
    """
    Convert a markdown string to a styled PDF.
    Returns raw bytes of the PDF.
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=f"Company Intelligence Report – {company_name}",
        author="AI Company Intelligence System",
    )

    S = _styles()
    story = []

    # ── Cover page ────────────────────────────────────────────────────────────
    cover_data = [
        [Paragraph(f"Company Intelligence Report", S["cover_title"])],
        [Paragraph(company_name, S["cover_sub"])],
        [Spacer(1, 0.1 * inch)],
        [Paragraph("AI-Powered Multi-Agent Analysis", S["cover_meta"])],
        [Paragraph(datetime.now().strftime("%B %d, %Y"), S["cover_meta"])],
        [Spacer(1, 0.05 * inch)],
        [Paragraph("Powered by CrewAI · Groq LLaMA · Serper", S["cover_meta"])],
    ]
    cover_table = Table(cover_data, colWidths=[doc.width])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("ROUNDEDCORNERS", [8]),
        ("TOPPADDING",   (0, 0), (-1, -1), 18),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 18),
        ("LEFTPADDING",  (0, 0), (-1, -1), 24),
        ("RIGHTPADDING", (0, 0), (-1, -1), 24),
        ("LINEBELOW",    (0, 1), (-1, 1), 1, GOLD),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 0.4 * inch))
    story.append(HRFlowable(width="100%", thickness=2, color=ACCENT))
    story.append(Spacer(1, 0.2 * inch))

    # ── Parse markdown lines ──────────────────────────────────────────────────
    lines = markdown_text.split("\n")
    i = 0
    in_table = False
    table_rows = []
    in_blockquote = False

    while i < len(lines):
        line = lines[i]

        # ── Markdown table detection ──
        if line.strip().startswith("|") and "|" in line[1:]:
            if not in_table:
                in_table = True
                table_rows = []
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            table_rows.append(cells)
            i += 1
            # skip separator row (---|---...)
            if i < len(lines) and re.match(r"^\|[\s\-|]+\|?$", lines[i]):
                i += 1
            continue

        if in_table:
            # flush table
            _flush_table(story, table_rows, S, doc.width)
            table_rows = []
            in_table = False

        # ── Headings ──
        if line.startswith("# "):
            text = _clean(line[2:].strip())
            story.append(Spacer(1, 0.1 * inch))
            story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT))
            story.append(Paragraph(text, S["h1"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
            story.append(Spacer(1, 0.05 * inch))

        elif line.startswith("## "):
            text = _clean(line[3:].strip())
            story.append(Paragraph(text, S["h2"]))

        elif line.startswith("### "):
            text = _clean(line[4:].strip())
            story.append(Paragraph(text, S["h3"]))

        elif line.startswith("#### "):
            text = _clean(line[5:].strip())
            story.append(Paragraph(f"<b>{text}</b>", S["body"]))

        # ── Blockquote ──
        elif line.startswith("> "):
            text = _clean(line[2:].strip())
            story.append(Paragraph(text, S["blockquote"]))

        # ── Horizontal rule ──
        elif line.strip() in ("---", "***", "___"):
            story.append(Spacer(1, 0.05 * inch))
            story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY))
            story.append(Spacer(1, 0.05 * inch))

        # ── Bullet list ──
        elif line.startswith("- ") or line.startswith("* "):
            text = _clean(line[2:].strip())
            # Detect confidence scores for special styling
            if "Confidence Score" in text or "/10" in text:
                story.append(Paragraph(
                    f"● {text}",
                    ParagraphStyle(
                        "conf_bullet",
                        parent=S["bullet"],
                        textColor=_confidence_color(text),
                        fontName="Helvetica-Bold",
                    )
                ))
            else:
                story.append(Paragraph(f"● {text}", S["bullet"]))

        # ── Numbered list ──
        elif re.match(r"^\d+\.\s", line):
            text = _clean(re.sub(r"^\d+\.\s", "", line).strip())
            num = re.match(r"^(\d+)\.", line).group(1)
            story.append(Paragraph(f"{num}. {text}", S["bullet"]))

        # ── Empty line ──
        elif line.strip() == "":
            story.append(Spacer(1, 0.06 * inch))

        # ── Regular paragraph ──
        else:
            text = _clean(line.strip())
            if text:
                # Source lines (start with [N])
                if re.match(r"^\[\d+\]", text):
                    story.append(Paragraph(text, S["source"]))
                else:
                    story.append(Paragraph(text, S["body"]))

        i += 1

    # flush any remaining table
    if in_table and table_rows:
        _flush_table(story, table_rows, S, doc.width)

    # ── Footer note ──────────────────────────────────────────────────────────
    story.append(Spacer(1, 0.3 * inch))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 0.1 * inch))
    story.append(Paragraph(
        f"<i>Confidential — Generated by AI Company Intelligence System on "
        f"{datetime.now().strftime('%B %d, %Y at %H:%M')} | "
        f"For internal use only</i>",
        ParagraphStyle(
            "footer",
            fontName="Helvetica-Oblique",
            fontSize=8,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
        )
    ))

    doc.build(story)
    return buf.getvalue()


def _flush_table(story, rows, S, page_width):
    """Render accumulated markdown table rows into a styled ReportLab Table."""
    if len(rows) < 1:
        return

    # Convert cells to Paragraph objects
    pdf_rows = []
    for r_idx, row in enumerate(rows):
        pdf_row = []
        for cell in row:
            style = S["table_header"] if r_idx == 0 else S["table_cell"]
            pdf_row.append(Paragraph(_clean(cell), style))
        pdf_rows.append(pdf_row)

    col_count = max(len(r) for r in rows)
    col_width = page_width / col_count

    t = Table(pdf_rows, colWidths=[col_width] * col_count, repeatRows=1)
    t.setStyle(TableStyle([
        # Header row
        ("BACKGROUND",   (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR",    (0, 0), (-1, 0), WHITE),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 9),
        # Alternating row shading
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BG]),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",     (0, 1), (-1, -1), 9),
        # Grid
        ("GRID",         (0, 0), (-1, -1), 0.4, MID_GRAY),
        ("LINEBELOW",    (0, 0), (-1, 0), 1.5, GOLD),
        # Padding
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
    ]))

    story.append(Spacer(1, 0.08 * inch))
    story.append(t)
    story.append(Spacer(1, 0.1 * inch))


def generate_pdf_from_file(filepath: str, company_name: str) -> bytes:
    """Read a markdown file and return PDF bytes."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Report file not found: {filepath}")
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return markdown_to_pdf(content, company_name)
