from adk.core.models import ChapterDraft
from adk.verification.stylometry import StylometryAuditGate


def test_stylometry_audit_gate():
    gate = StylometryAuditGate()
    chapters = [
        ChapterDraft(
            number=1,
            title="Wstęp",
            content_typst="To jest przykładowy tekst pracy inżynierskiej. Zawiera różne słowa i pojęcia technologiczne.",
            summary="s",
        )
    ]
    report = gate.audit_chapters(chapters)
    assert report.total_words > 0
    assert report.ttr > 0.0
    assert "JSA" in report.estimated_jsa_risk or "NISKIE" in report.estimated_jsa_risk or "UMIARKOWANE" in report.estimated_jsa_risk

