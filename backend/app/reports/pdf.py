from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, ListFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .llm import IncidentReport

RISK_COLORS = {"critical": "#b91c1c", "high": "#dc2626", "medium": "#d97706", "low": "#2563eb"}


def render_pdf(path: Path, incident: dict, title: str, report: IncidentReport, snapshot: Path):
    styles = getSampleStyleSheet()
    body, h2 = styles["BodyText"], styles["Heading2"]

    def p(text):
        return Paragraph(escape(text), body)

    def bullets(items):
        return ListFlowable([p(i) for i in items], bulletType="bullet", leftIndent=12)

    risk = report.risk_level.lower()
    details = Table(
        [
            ["Incident ID", f"#{incident['id']}"],
            ["Date / time", incident["time"]],
            ["Location", incident["zone"]],
            ["Camera", f"{incident['camera_name']} ({incident['camera_id']})"],
            ["Violation", title],
            ["Detector confidence", f"{incident['confidence']:.0%}"],
            ["Risk level", risk.upper()],
        ],
        colWidths=[4.5 * cm, 12 * cm],
    )
    details.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (1, 6), (1, 6), colors.HexColor(RISK_COLORS.get(risk, "#000000"))),
        ("FONTNAME", (1, 6), (1, 6), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    image = Image(str(snapshot))
    image._restrictSize(16.5 * cm, 9 * cm)

    story = [
        Paragraph("Safety Incident Report", styles["Title"]),
        Paragraph("Smart-EHS automated monitoring", styles["Italic"]),
        Spacer(1, 0.4 * cm),
        details,
        Spacer(1, 0.4 * cm),
        image,
        Paragraph("Summary", h2), p(report.summary),
        Paragraph("Observed conditions", h2), p(report.observed_conditions),
        Paragraph("Applicable regulations", h2),
        bullets([f"{c.standard} - {c.title}: {c.relevance}" for c in report.citations] or ["None identified."]),
        Paragraph("Immediate actions", h2), bullets(report.immediate_actions),
        Paragraph("Preventive recommendations", h2), bullets(report.preventive_recommendations),
        Paragraph("Notify", h2), p(report.notify),
    ]
    SimpleDocTemplate(str(path), pagesize=A4, title=f"Incident #{incident['id']}",
                      leftMargin=2 * cm, rightMargin=2 * cm, topMargin=1.5 * cm, bottomMargin=1.5 * cm).build(story)
