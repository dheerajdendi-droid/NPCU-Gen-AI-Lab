"""Tests for evaluation ratios, configuration, and human review."""

import pytest
from pydantic import ValidationError

from cu_intelligence.evaluation import (
    EvaluationConfig,
    HumanReviewDisposition,
    HumanReviewResult,
    RatioMetric,
    ratio_metric,
)


def test_zero_denominator_is_explicitly_not_applicable() -> None:
    metric = ratio_metric(0, 0)

    assert metric.numerator == 0
    assert metric.denominator == 0
    assert metric.value is None


def test_ratio_is_rounded_to_four_places() -> None:
    assert ratio_metric(2, 3).value == 0.6667


@pytest.mark.parametrize(
    ("numerator", "denominator", "value"),
    [(1, 0, None), (0, 0, 0), (1, 2, 0.4)],
)
def test_inconsistent_ratio_values_are_rejected(
    numerator: float,
    denominator: int,
    value: float | None,
) -> None:
    with pytest.raises(ValidationError):
        RatioMetric(numerator=numerator, denominator=denominator, value=value)


def test_pending_human_review_has_no_automated_ratings() -> None:
    review = HumanReviewResult(case_id="case-one")

    assert review.disposition is HumanReviewDisposition.PENDING
    assert review.correctness is None


def test_pending_human_review_rejects_a_rating() -> None:
    with pytest.raises(ValidationError, match="pending reviews"):
        HumanReviewResult(case_id="case-one", correctness=2)


def test_completed_human_review_requires_all_ratings() -> None:
    with pytest.raises(ValidationError, match="all six ratings"):
        HumanReviewResult(
            case_id="case-one",
            correctness=2,
            disposition=HumanReviewDisposition.ACCEPT,
        )


def test_evaluation_configuration_cannot_tune_the_accepted_baseline() -> None:
    with pytest.raises(ValidationError, match="retrieval depth"):
        EvaluationConfig(retrieval_depth=5)
