"""Test dei contratti di dashboard/sources.py (loader e helper)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "dashboard"))

import sources  # noqa: E402


def test_tables_contract():
    """I loader coprono esattamente i mart pubblicati dal compose."""
    assert set(sources._TABLES) == {
        "mart_hub",
        "mart_settori",
        "mart_settori_trend",
        "mart_trend_integrato",
        "mart_domanda",
        "mart_trimestrale",
        "mart_riconciliazione",
        "mart_pil_componenti",
        "mart_imprese_sintesi",
    }


def test_mart_url_gcs_fallback(monkeypatch):
    """Senza parquet locali, l'URL risolve sul path GCS del registry."""
    monkeypatch.setattr(sources, "_MART_DIR", Path("/nonexistent/pil"))
    assert sources._mart_url("mart_hub") == (
        "https://storage.googleapis.com/dataciviclab-mart/"
        "pil-intelligence/pil_intelligence/2026/mart_hub.parquet"
    )


def test_mart_url_local_preferred(tmp_path, monkeypatch):
    """Se il parquet locale esiste, vince il path locale."""
    monkeypatch.setattr(sources, "_MART_DIR", tmp_path)
    (tmp_path / "mart_hub.parquet").write_bytes(b"")
    assert sources._mart_url("mart_hub") == str(tmp_path / "mart_hub.parquet")


def test_macro_area():
    assert sources.macro_area("ITC11") == "Nord-Ovest"
    assert sources.macro_area("ITG11") == "Isole"
    assert sources.macro_area("XXX") == "Altro"


def test_delta_pct_threshold():
    assert sources.delta_pct(110, 100) == "+10.0%"
    assert sources.delta_pct(100.05, 100) is None  # sotto soglia
    assert sources.delta_pct(None, 100) is None
    assert sources.delta_pct(100, 0) is None


def test_delta_pp():
    assert sources.delta_pp(5.0, 4.0) == "+1.0pp"
    assert sources.delta_pp(4.01, 4.0) is None
    assert sources.delta_pp(None, 4.0) is None
