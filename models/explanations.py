"""Plain-language explanations for model outputs."""

from models.scoring import Assessment


def explain_assessment(assessment: Assessment, scene: dict[str, object]) -> str:
    """Describe what drove an assessment without overstating certainty."""
    return (
        f"The current model gives this {scene['region']} scene a {assessment.label} assessment "
        f"with a provisional score of {assessment.score:.1f}/100. "
        "This result reflects the selected indicators and configured weights; it is not a legal, engineering, or hazard determination."
    )