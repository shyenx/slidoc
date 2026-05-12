"""Tests for slidoc.utils."""

import tempfile
import time
from pathlib import Path

from slidoc.utils import fmt_duration, fmt_ts, is_newer, parse_index_prefix


def test_fmt_ts():
    assert fmt_ts(0) == "00:00:00"
    assert fmt_ts(59) == "00:00:59"
    assert fmt_ts(60) == "00:01:00"
    assert fmt_ts(3661) == "01:01:01"
    assert fmt_ts(36000) == "10:00:00"


def test_fmt_duration():
    assert fmt_duration(5) == "5s"
    assert fmt_duration(65) == "1m05s"
    assert fmt_duration(3700) == "1h01m"


def test_parse_index_prefix():
    assert parse_index_prefix("1-speaker-topic") == 1
    assert parse_index_prefix("12-anything") == 12
    assert parse_index_prefix("1. dot prefix") == 1
    assert parse_index_prefix("3_underscore") == 3
    assert parse_index_prefix("3 space") == 3
    assert parse_index_prefix("no-prefix") is None
    assert parse_index_prefix("") is None


def test_is_newer_target_missing():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        dep = d / "dep"
        dep.touch()
        target = d / "target"
        assert is_newer(target, dep) is False


def test_is_newer_target_newer_than_deps():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        dep = d / "dep"
        dep.touch()
        time.sleep(0.05)
        target = d / "target"
        target.touch()
        assert is_newer(target, dep) is True


def test_is_newer_dep_newer_than_target():
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        target = d / "target"
        target.touch()
        time.sleep(0.05)
        dep = d / "dep"
        dep.touch()
        assert is_newer(target, dep) is False


def test_is_newer_missing_dep_ignored():
    """A dep that doesn't exist should not invalidate cache."""
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        target = d / "target"
        target.touch()
        missing = d / "missing"
        assert is_newer(target, missing) is True
