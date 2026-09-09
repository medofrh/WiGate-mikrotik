"""Druckfertiger Gutscheinbogen: A4, 2 x 5 Gutscheine pro Seite.

Die QR-Codes zeichnet ReportLab selbst als Vektor, deshalb werden weder
``qrcode`` noch ``Pillow`` benötigt und der Druck bleibt in jeder Größe scharf.
"""

from __future__ import annotations

import io
import unicodedata
from typing import Iterable

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .generator import BLANK_LABEL, GeneratedUser

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 10 * mm
COLUMNS = 2
ROWS = 5
PER_PAGE = COLUMNS * ROWS
CELL_WIDTH = (PAGE_WIDTH - 2 * MARGIN) / COLUMNS
CELL_HEIGHT = (PAGE_HEIGHT - 2 * MARGIN) / ROWS
PADDING = 6 * mm
QR_SIZE = 30 * mm
TEXT_GAP = 4 * mm

# Höhe des Textblocks (Summe der Zeilenabstände unten), damit er optisch
# mittig im Gutschein sitzt.
CONTENT_HEIGHT = 90.0

VOUCHER_TITLE = "WLAN-ZUGANG"
LABEL_USER = "BENUTZER"
LABEL_PASSWORD = "PASSWORT"

INK = HexColor("#111827")
MUTED = HexColor("#6b7280")
CUT_LINE = HexColor("#c9ced6")


def _safe(text: str) -> str:
    """Macht Text für die Standardschriften (WinAnsi) darstellbar."""
    if not text:
        return ""
    try:
        text.encode("cp1252")
        return text
    except UnicodeEncodeError:
        pass
    decomposed = unicodedata.normalize("NFKD", text)
    result = []
    for char in decomposed:
        if unicodedata.combining(char):
            continue
        try:
            char.encode("cp1252")
            result.append(char)
        except UnicodeEncodeError:
            result.append("?")
    return "".join(result)


def _fit(
    pdf: canvas.Canvas, text: str, font: str, size: float, max_width: float, min_size: float = 6.0
) -> tuple[str, float]:
    """Verkleinert bzw. kürzt Text, bis er in die Spalte passt."""
    text = _safe(text)
    while size > min_size and pdf.stringWidth(text, font, size) > max_width:
        size -= 0.5
    if pdf.stringWidth(text, font, size) > max_width:
        while text and pdf.stringWidth(text + "…", font, size) > max_width:
            text = text[:-1]
        text += "…"
    return text, size


def _draw_qr(pdf: canvas.Canvas, value: str, x: float, y: float, size: float) -> None:
    widget = QrCodeWidget(value or " ", barLevel="M", barBorder=2)
    bounds = widget.getBounds()
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    drawing = Drawing(
        size,
        size,
        transform=[
            size / width,
            0,
            0,
            size / height,
            -bounds[0] * size / width,
            -bounds[1] * size / height,
        ],
    )
    drawing.add(widget)
    renderPDF.draw(drawing, pdf, x, y)


def _draw_voucher(pdf: canvas.Canvas, user: GeneratedUser, index_on_page: int) -> None:
    column = index_on_page % COLUMNS
    row = index_on_page // COLUMNS
    left = MARGIN + column * CELL_WIDTH
    top = PAGE_HEIGHT - MARGIN - row * CELL_HEIGHT
    bottom = top - CELL_HEIGHT

    # Schnittlinie
    pdf.saveState()
    pdf.setStrokeColor(CUT_LINE)
    pdf.setLineWidth(0.4)
    pdf.setDash(2, 2)
    pdf.rect(left, bottom, CELL_WIDTH, CELL_HEIGHT, stroke=1, fill=0)
    pdf.restoreState()

    qr_x = left + CELL_WIDTH - PADDING - QR_SIZE
    qr_y = bottom + (CELL_HEIGHT - QR_SIZE) / 2
    _draw_qr(pdf, user.qr, qr_x, qr_y, QR_SIZE)

    text_x = left + PADDING
    text_width = CELL_WIDTH - 2 * PADDING - QR_SIZE - TEXT_GAP
    slack = max(0.0, CELL_HEIGHT - 2 * PADDING - CONTENT_HEIGHT)
    cursor = top - PADDING - slack / 2

    cursor -= 7
    pdf.setFillColor(MUTED)
    pdf.setFont("Helvetica", 6.5)
    pdf.drawString(text_x, cursor, VOUCHER_TITLE)

    cursor -= 18
    name = BLANK_LABEL if user.blank else user.display_name
    fitted, size = _fit(pdf, name, "Helvetica-Bold", 11.5, text_width)
    pdf.setFillColor(INK)
    pdf.setFont("Helvetica-Bold", size)
    pdf.drawString(text_x, cursor, fitted)

    cursor -= 12
    if not user.blank and user.birthday:
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 8.5)
        pdf.drawString(text_x, cursor, _safe(user.birthday))

    for label, value in ((LABEL_USER, user.username), (LABEL_PASSWORD, user.password)):
        cursor -= 18 if label == LABEL_USER else 13
        pdf.setFillColor(MUTED)
        pdf.setFont("Helvetica", 6.5)
        pdf.drawString(text_x, cursor, label)
        cursor -= 11
        fitted, size = _fit(pdf, value, "Courier-Bold", 10.5, text_width)
        pdf.setFillColor(INK)
        pdf.setFont("Courier-Bold", size)
        pdf.drawString(text_x, cursor, fitted)


def pages_needed(count: int) -> int:
    return max(1, -(-count // PER_PAGE))


def build_vouchers(users: Iterable[GeneratedUser]) -> bytes:
    users = list(users)
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Gutscheine")
    pdf.setAuthor("WiGate")

    for index, user in enumerate(users):
        if index and index % PER_PAGE == 0:
            pdf.showPage()
        _draw_voucher(pdf, user, index % PER_PAGE)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
