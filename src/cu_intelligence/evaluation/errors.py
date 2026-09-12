"""Application-owned errors for evaluation data and execution."""


class EvaluationError(Exception):
    """Base error for the provider-independent evaluation boundary."""


class EvaluationDatasetError(EvaluationError):
    """Raised when a synthetic evaluation dataset is missing or invalid."""
