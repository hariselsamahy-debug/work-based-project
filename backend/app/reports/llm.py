"""Asks Claude to write the incident report from the snapshot + retrieved OSHA text.

The model returns structured fields (not free text) so the PDF layout stays ours.
Without an API key a template report is produced instead, so the app still works offline.
"""
import base64
import logging

import anthropic
from pydantic import BaseModel

from .osha_index import Chunk

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an occupational safety (EHS) officer writing formal incident reports for a \
factory manager. You receive a camera snapshot where an automated system flagged a safety violation \
(red boxes), the incident metadata, and excerpts from OSHA regulations.

Write factually about what is visible in the image. If the image does not clearly show the flagged \
violation, say so in the summary and lower the risk level - the detector can be wrong. Cite only \
OSHA standards that appear in the provided excerpts or in the suggested standards list, and never \
invent section numbers or quotations."""


class Citation(BaseModel):
    standard: str  # e.g. "29 CFR 1910.135"
    title: str
    relevance: str


class IncidentReport(BaseModel):
    summary: str
    observed_conditions: str
    citations: list[Citation]
    risk_level: str  # low / medium / high / critical
    immediate_actions: list[str]
    preventive_recommendations: list[str]
    notify: str


def _context_text(incident: dict, violation: dict, chunks: list[Chunk]) -> str:
    excerpts = "\n\n".join(
        f"[{i}] {c.source}, page {c.page}:\n{c.text}" for i, c in enumerate(chunks, start=1)
    ) or "(No OSHA documents are loaded; rely on the suggested standards only.)"
    return f"""Incident metadata:
- Incident ID: {incident['id']}
- Time: {incident['time']}
- Camera: {incident['camera_name']} ({incident['camera_id']})
- Location: {incident['zone']}
- Violation detected: {violation['title']} (type {incident['type']})
- Detector confidence: {incident['confidence']:.0%}
- System severity: {incident['severity']}
- Suggested OSHA standards: {', '.join(violation['standards']) or 'none'}

OSHA excerpts:
{excerpts}

Write the incident report."""


def write_report(client: anthropic.Anthropic | None, model: str, incident: dict, violation: dict,
                 chunks: list[Chunk], snapshot_jpeg: bytes) -> IncidentReport:
    if client is None:
        return template_report(incident, violation)

    response = client.beta.messages.parse(
        model=model,
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": base64.standard_b64encode(snapshot_jpeg).decode("ascii"),
                }},
                {"type": "text", "text": _context_text(incident, violation, chunks)},
            ],
        }],
        output_format=IncidentReport,
        # If a safety classifier declines, the API retries on Anthropic's recommended fallback model.
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    )
    if response.stop_reason == "refusal" or response.parsed_output is None:
        log.warning("Claude returned no report (stop_reason=%s); using template", response.stop_reason)
        return template_report(incident, violation)
    return response.parsed_output


def template_report(incident: dict, violation: dict) -> IncidentReport:
    return IncidentReport(
        summary=(f"At {incident['time']} in {incident['zone']}, camera {incident['camera_name']} "
                 f"detected: {violation['title']} (confidence {incident['confidence']:.0%})."),
        observed_conditions="Automatically generated report (LLM not configured). See the attached snapshot.",
        citations=[Citation(standard=s, title=violation["title"], relevance="Applicable standard for this violation type.")
                   for s in violation["standards"]],
        risk_level=incident["severity"],
        immediate_actions=["Notify the area supervisor.", "Verify the situation on site and correct it."],
        preventive_recommendations=["Review PPE requirements with the shift team."],
        notify="Area supervisor",
    )
