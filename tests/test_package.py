"""Package-level smoke tests (version, public API surface)."""

import importlib
import re
from unittest.mock import patch

import pytest

import inventory


def test_version_is_pep440_ish():
    # PEP 440-ish: N(.N)+ with optional pre/post/dev/local suffix.
    # Intentionally NOT pinned to a specific value so bumps don't require
    # a test edit; the authoritative version lives in pyproject.toml and
    # is surfaced via importlib.metadata at import time.
    assert isinstance(inventory.__version__, str)
    assert re.match(
        r"^\d+(\.\d+)+((a|b|rc)\d+)?(\.post\d+)?"
        r"(\.dev\d+)?(\+[A-Za-z0-9.]+)?$",
        inventory.__version__,
    ), f"not PEP 440-ish: {inventory.__version__!r}"


def test_version_in_all():
    assert "__version__" in inventory.__all__


# ---------------------------------------------------------------------------
# Version-sourcing paths (issue #2).
#
# `inventory.__version__` is resolved at import time from
# `importlib.metadata.version("inventory-pricing")`, with a
# `PackageNotFoundError` fallback to the `"0.0.0+local"` sentinel. Both
# branches are exercised here by mocking the metadata lookup and reloading
# the package, so the tests are deterministic regardless of whether this
# machine has the dist installed, editable-installed, or neither.
#
# We patch `importlib.metadata.version` (the underlying function) rather
# than the module-level `_dist_version` alias inside `inventory`, because
# the alias is bound at `inventory`'s import time — patching the original
# ensures the reloaded module picks up the mock.
# ---------------------------------------------------------------------------

@pytest.fixture
def reloaded_inventory():
    """Reload `inventory` inside a test and restore the original after.

    Reloading re-executes the module body, which re-runs the
    `try/except PackageNotFoundError` block and re-binds `__version__`.
    Without the restore step, later tests in the same session would see
    whatever mocked value the last test produced.
    """
    original_version = inventory.__version__
    try:
        yield importlib.reload(inventory)
    finally:
        # Reload once more with the real metadata lookup active so
        # subsequent tests see the true __version__ again. Also
        # defensively restore the attribute in case the final reload
        # itself tripped the fallback for some reason.
        importlib.reload(inventory)
        inventory.__version__ = original_version


def test_version_from_installed_dist_metadata(reloaded_inventory):
    """Happy path: when the dist is registered, __version__ reflects it."""
    with patch("importlib.metadata.version", return_value="1.2.3") as mock_v:
        reloaded = importlib.reload(inventory)
        assert reloaded.__version__ == "1.2.3"
        # Confirms we looked up the *distribution* name, not the import
        # name — this is the bug the issue exists to prevent.
        mock_v.assert_called_once_with("inventory-pricing")


def test_version_falls_back_to_local_sentinel_when_dist_not_found(
    reloaded_inventory,
):
    """Fallback path: uninstalled source checkout → "0.0.0+local"."""
    from importlib.metadata import PackageNotFoundError

    with patch(
        "importlib.metadata.version",
        side_effect=PackageNotFoundError("inventory-pricing"),
    ):
        reloaded = importlib.reload(inventory)
        assert reloaded.__version__ == "0.0.0+local"
        # Sentinel must still satisfy the PEP 440-ish regex so downstream
        # code that validates __version__ doesn't choke on a source
        # checkout. This is the same regex used in
        # test_version_is_pep440_ish above, kept in sync intentionally.
        assert re.match(
            r"^\d+(\.\d+)+((a|b|rc)\d+)?(\.post\d+)?"
            r"(\.dev\d+)?(\+[A-Za-z0-9.]+)?$",
            reloaded.__version__,
        ), reloaded.__version__
