"""Repository-wide pytest safety controls."""

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    """Require an explicit command-line opt-in before any live test can run."""

    parser.addoption(
        "--run-live",
        action="store_true",
        default=False,
        help="run tests marked live that may call external providers and incur cost",
    )


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    """Skip live tests unless the invocation includes ``--run-live``."""

    if config.getoption("--run-live"):
        return

    skip_live = pytest.mark.skip(
        reason="live provider tests require the explicit --run-live option"
    )
    for item in items:
        if "live" in item.keywords:
            item.add_marker(skip_live)
