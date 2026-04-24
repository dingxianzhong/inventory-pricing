"""Package-level smoke tests (version, public API surface)."""

import re

import inventory


def test_version_is_pep440_ish():
    # PEP 440-ish: N(.N)+ with optional pre/post/dev/local suffix.
    # Intentionally NOT pinned to a specific value so bumps don't require
    # a test edit; the authoritative version lives in pyproject.toml and
    # inventory/__init__.py.
    assert isinstance(inventory.__version__, str)
    assert re.match(
        r"^\d+(\.\d+)+((a|b|rc)\d+)?(\.post\d+)?(\.dev\d+)?(\+[A-Za-z0-9.]+)?$",
        inventory.__version__,
    ), f"not PEP 440-ish: {inventory.__version__!r}"


def test_version_in_all():
    assert "__version__" in inventory.__all__
