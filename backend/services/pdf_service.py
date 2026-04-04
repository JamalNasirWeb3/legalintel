"""Generate a PDF report from structured report data using fpdf2."""

import io
import re
from datetime import datetime

import httpx
from fpdf import FPDF

# Characters outside Latin-1 that commonly appear in AI-generated text
_UNICODE_REPLACEMENTS = str.maketrans({
    "\u2014": "--",   # em dash  —
    "\u2013": "-",    # en dash  –
    "\u2012": "-",    # figure dash
    "\u2010": "-",    # hyphen
    "\u2011": "-",    # non-breaking hyphen
    "\u2018": "'",    # left single quote  '
    "\u2019": "'",    # right single quote / apostrophe  '
    "\u201c": '"',    # left double quote  "
    "\u201d": '"',    # right double quote  "
    "\u2026": "...",  # ellipsis  …
    "\u2022": "-",    # bullet  •
    "\u00b7": ".",    # middle dot  ·
    "\u00ae": "(R)",  # registered  ®
    "\u00a9": "(C)",  # copyright  ©
    "\u2122": "(TM)", # trade mark  ™
    "\u00a0": " ",    # non-breaking space
})


def _clean(text: str) -> str:
    """Replace known Unicode punctuation with ASCII equivalents, then drop
    any remaining characters that Helvetica (Latin-1) cannot encode."""
    text = text.translate(_UNICODE_REPLACEMENTS)
    # Drop anything still outside Latin-1 rather than crash
    return text.encode("latin-1", errors="ignore").decode("latin-1")


class _ReportPDF(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self._doc_title = title

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_fill_color(17, 24, 39)   # gray-900
        self.set_text_color(255, 255, 255)
        self.rect(0, 0, 210, 14, "F")
        self.set_xy(8, 3)
        self.cell(0, 8, "Legal Intelligence System", align="L")
        self.set_xy(0, 3)
        self.cell(w=202, h=8, text=_clean(self._doc_title), align="R")
        self.set_text_color(0, 0, 0)
        self.ln(18)

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, f"Page {self.page_no()}  |  Confidential  |  For attorney use only", align="C")

    def section_title(self, text: str):
        self.set_font("Helvetica", "B", 11)
        self.set_fill_color(239, 246, 255)   # blue-50
        self.set_text_color(30, 64, 175)     # blue-800
        self.cell(0, 8, _clean(text), new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, _clean(text))
        self.ln(3)

    def bullet(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_x(self.l_margin + 4)
        self.cell(5, 6, "-")
        self.multi_cell(0, 6, _clean(text))


def _fetch_photo(url: str) -> bytes | None:
    """Download an image from a URL; return bytes or None on failure."""
    if not url:
        return None
    try:
        r = httpx.get(url, timeout=10, follow_redirects=True)
        if r.status_code == 200:
            return r.content
    except Exception:
        pass
    return None


def generate_report_pdf(report: dict) -> bytes:
    """Return a PDF as raw bytes given a report dict."""
    subject_name = report.get("subject_name", "Unknown Subject")
    created_at_raw = report.get("created_at", "")
    try:
        dt = datetime.fromisoformat(str(created_at_raw).replace("Z", "+00:00"))
        created_str = dt.strftime("%B %d, %Y at %H:%M UTC")
    except Exception:
        created_str = str(created_at_raw)

    confidence = report.get("confidence_score")
    confidence_str = f"{round(confidence * 100)}%" if confidence is not None else "N/A"

    photo_bytes = _fetch_photo(report.get("photo_url"))

    pdf = _ReportPDF(title=f"Report: {subject_name}")
    pdf.set_margins(left=14, top=14, right=14)
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # ── Cover block ──────────────────────────────────────────────────────────
    PHOTO_W = 38          # mm
    PHOTO_H = 46          # mm  (~1.2 portrait ratio)
    PHOTO_X = 210 - 14 - PHOTO_W   # flush with right margin
    TEXT_W  = 182 - PHOTO_W - 6    # remaining width minus gap

    cover_y = pdf.get_y()

    if photo_bytes:
        # Text block on the left, photo floated to the right
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(TEXT_W, 10, "Investigation Report", new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", "", 12)
        pdf.cell(TEXT_W, 8, _clean(subject_name), new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(TEXT_W, 6, _clean(f"Generated {created_str}"),
                 new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.cell(TEXT_W, 6, _clean(f"Confidence: {confidence_str}"),
                 new_x="LMARGIN", new_y="NEXT", align="L")
        pdf.set_text_color(0, 0, 0)

        # Place photo at absolute position (top-right of cover block)
        try:
            pdf.image(io.BytesIO(photo_bytes), x=PHOTO_X, y=cover_y, w=PHOTO_W, h=PHOTO_H)
        except Exception:
            pass  # If image fails, cover still looks fine without it

        # Advance past whichever is taller: text block or photo
        text_bottom = pdf.get_y()
        photo_bottom = cover_y + PHOTO_H
        pdf.set_y(max(text_bottom, photo_bottom))
    else:
        # Original centered layout when no photo is available
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, "Investigation Report", new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 7, _clean(subject_name), new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_font("Helvetica", "I", 9)
        pdf.set_text_color(100, 100, 100)
        pdf.cell(0, 6, _clean(f"Generated {created_str}   |   Confidence: {confidence_str}"),
                 new_x="LMARGIN", new_y="NEXT", align="C")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(6)
    pdf.line(14, pdf.get_y(), 196, pdf.get_y())
    pdf.ln(6)

    # ── Executive Summary ────────────────────────────────────────────────────
    if report.get("executive_summary"):
        pdf.section_title("Executive Summary")
        pdf.body_text(report["executive_summary"])

    # ── Risk Flags ───────────────────────────────────────────────────────────
    risk_flags = report.get("risk_flags") or []
    if risk_flags:
        pdf.section_title("Risk Flags")
        for flag in risk_flags:
            pdf.bullet(flag)
        pdf.ln(3)

    # ── Asset Summary ────────────────────────────────────────────────────────
    if report.get("asset_summary"):
        pdf.section_title("Asset Summary")
        pdf.body_text(report["asset_summary"])

    # ── Full Report ──────────────────────────────────────────────────────────
    if report.get("full_report_md"):
        pdf.section_title("Full Report")
        plain = re.sub(r"#{1,6}\s*", "", report["full_report_md"])
        plain = re.sub(r"\*{1,2}(.+?)\*{1,2}", r"\1", plain)
        plain = re.sub(r"__(.+?)__", r"\1", plain)
        pdf.body_text(plain)  # body_text calls _clean internally

    # ── Sources Consulted ────────────────────────────────────────────────────
    sources = report.get("sources_consulted") or []
    if sources:
        pdf.section_title("Sources Consulted")
        for i, src in enumerate(sources, 1):
            pdf.set_font("Helvetica", "", 9)
            pdf.set_x(pdf.l_margin + 4)
            pdf.cell(8, 6, f"{i}.")
            pdf.multi_cell(0, 6, _clean(src))
        pdf.ln(3)

    return bytes(pdf.output())
