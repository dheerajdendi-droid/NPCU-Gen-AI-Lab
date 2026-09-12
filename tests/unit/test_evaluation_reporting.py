"""Tests for stable fingerprints and readable report primitives."""

from cu_intelligence.evaluation import (
    HumanReviewDisposition,
    HumanReviewResult,
    fingerprint_value,
    ratio_metric,
    render_human_review_template,
)


def test_fingerprint_is_independent_of_mapping_key_order() -> None:
    first = {"b": [2, 1], "a": {"value": "synthetic"}}
    second = {"a": {"value": "synthetic"}, "b": [2, 1]}

    assert fingerprint_value(first) == fingerprint_value(second)
    assert len(fingerprint_value(first)) == 64


def test_human_review_template_keeps_pending_ratings_visible() -> None:
    template = render_human_review_template(HumanReviewResult(case_id="case-one"))

    assert "Correctness: _pending (0/1/2)_" in template
    assert "Final disposition: `PENDING`" in template


def test_completed_human_review_renders_all_ratings_and_notes() -> None:
    review = HumanReviewResult(
        case_id="case-one",
        correctness=2,
        completeness=1,
        relevance=2,
        appropriate_evidence_use=2,
        clarity=1,
        version_status_handling=2,
        reviewer_notes="Needs a clearer summary.",
        disposition=HumanReviewDisposition.REVISE,
    )

    template = render_human_review_template(review)

    assert "Correctness: 2" in template
    assert "Needs a clearer summary." in template
    assert "Final disposition: `REVISE`" in template


def test_rounding_retains_the_underlying_numerator_and_denominator() -> None:
    metric = ratio_metric(2, 3)

    assert metric.numerator == 2
    assert metric.denominator == 3
    assert metric.value == 0.6667
