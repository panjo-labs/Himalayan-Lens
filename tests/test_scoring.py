import numpy as np
import pytest

from indicators.demo_data import build_demo_scene
from models.explanations import explain_assessment
from models.scoring import assess_scene


def test_demo_scene_produces_bounded_assessment():
    scene = build_demo_scene("Central Uttarakhand demo")
    assessment = assess_scene(scene)
    assert 0 <= assessment.score <= 100
    assert assessment.label in {"Green", "Yellow", "Red"}
    assert assessment.reasons


def test_missing_indicator_is_reported():
    with pytest.raises(ValueError, match="missing required indicators"):
        assess_scene({"slope": np.ones((2, 2))})


def test_explanation_names_assessment_and_limitations():
    scene = build_demo_scene("Kumaon demo")
    assessment = assess_scene(scene)
    explanation = explain_assessment(assessment, scene)
    assert assessment.label in explanation
    assert "not a legal" in explanation