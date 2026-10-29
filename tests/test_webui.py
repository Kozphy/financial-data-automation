"""Smoke test for the local Streamlit UI."""

from __future__ import annotations

from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "streamlit_app.py"
SAMPLE = ROOT / "data" / "sample" / "sample_transactions.csv"


def test_app_shows_uploader_and_cleans_a_file() -> None:
    app = AppTest.from_file(str(APP), default_timeout=60)
    app.run()
    assert not app.exception
    assert app.file_uploader
    assert app.button

    app.file_uploader[0].upload("sample_transactions.csv", SAMPLE.read_bytes()).run()
    app.button[0].click().run()
    assert not app.exception, app.exception
    values = [str(metric.value) for metric in app.metric]
    assert "9" in values
    assert "4" in values
    assert "5" in values
