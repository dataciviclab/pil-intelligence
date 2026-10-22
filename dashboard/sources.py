"""Data sources + aggregation helpers for PIL Intelligence dashboard.

Legge i mart da GCS in produzione, dai parquet locali in sviluppo
(pattern condiviso: `out/data/mart/<slug>/<year>/` se presente, altrimenti
`https://storage.googleapis.com/dataciviclab-mart/...`).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

PREFIX = "pil-intelligence/"
SLUG = "pil_intelligence"
YEAR = 2026

_REPO = Path(__file__).parent.parent
_MART_DIR = _REPO / "out" / "data" / "mart" / SLUG / str(YEAR)

_TABLES = (
    "mart_hub",
    "mart_settori",
    "mart_settori_trend",
    "mart_trend_integrato",
    "mart_domanda",
    "mart_trimestrale",
    "mart_riconciliazione",
    "mart_pil_componenti",
    "mart_imprese_sintesi",
    "mart_convergenza",
)

MACRO_SECTORS = ("A", "B-E", "F", "G-J", "K-N", "O-U", "R-U")

_MACRO_MAP = {
    "ITC": "Nord-Ovest",
    "ITH": "Nord-Est",
    "ITI": "Centro",
    "ITF": "Sud",
    "ITG": "Isole",
}


# --- Connection ---

def _mart_url(table: str) -> str:
    """Path locale se `out/` è presente, altrimenti URL pubblico GCS."""
    local = _MART_DIR / f"{table}.parquet"
    if local.exists():
        return str(local)
    from lab_connectors.gcs.paths import https_url

    return https_url("mart", "mart_parquet", slug=SLUG, year=YEAR, table=table, prefix=PREFIX)


@st.cache_resource(show_spinner=False)
def _con():
    import duckdb

    con = duckdb.connect(":memory:")
    for t in _TABLES:
        con.execute(f"CREATE TABLE {t} AS SELECT * FROM read_parquet('{_mart_url(t)}')")
    return con


def query(sql: str) -> pd.DataFrame:
    return _con().execute(sql).fetchdf()


def macro_area(geo: str) -> str:
    return _MACRO_MAP.get(geo[:3], "Altro")


# --- National aggregation ---

def _nat(year: int, col: str) -> float | None:
    r = query(f"SELECT SUM({col}) AS v FROM mart_hub WHERE country='IT' AND year={year} AND {col} IS NOT NULL")
    v = r.iloc[0]["v"] if len(r) > 0 else None
    return float(v) if v is not None else None


def _wavg(year: int, val_col: str, weight_col: str) -> float | None:
    r = query(
        f"SELECT SUM({val_col} * {weight_col}) / SUM({weight_col}) AS v "
        f"FROM mart_hub WHERE country='IT' AND year={year} "
        f"AND {val_col} IS NOT NULL AND {weight_col} IS NOT NULL"
    )
    v = r.iloc[0]["v"] if len(r) > 0 else None
    return float(v) if v is not None else None


def delta_pct(curr, prev, threshold=0.1):
    """Percent change. Hides if below threshold."""
    if curr is None or prev is None or prev == 0:
        return None
    pct = (curr / prev - 1) * 100
    return f"{pct:+.1f}%" if abs(pct) >= threshold else None


def delta_pp(curr, prev):
    """Percentage point change."""
    if curr is None or prev is None:
        return None
    d = curr - prev
    return f"{d:+.1f}pp" if abs(d) >= 0.05 else None


# --- Data loaders ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_hub() -> pd.DataFrame:
    return query("SELECT * FROM mart_hub WHERE country = 'IT' ORDER BY year, geo")


def latest_hub_year() -> int:
    r = query("SELECT MAX(year) AS y FROM mart_hub WHERE country='IT' AND pil_procapite_eur IS NOT NULL")
    return int(r.iloc[0]["y"])


@st.cache_data(ttl=3600, show_spinner=False)
def load_hub_anno(year: int) -> pd.DataFrame:
    return query(f"SELECT * FROM mart_hub WHERE country='IT' AND year={year} ORDER BY pil_procapite_eur DESC")


@st.cache_data(ttl=3600, show_spinner=False)
def load_settori() -> pd.DataFrame:
    return query(
        "SELECT * FROM mart_settori WHERE country = 'IT' "
        "AND nace_r2 IN ('A','B-E','F','G-J','K-N','O-U','R-U') "
        "ORDER BY year, geo, gva_valore_mio DESC"
    )


def latest_settori_year() -> int:
    r = query("SELECT MAX(year) AS y FROM mart_settori WHERE country='IT' AND gva_valore_mio IS NOT NULL")
    return int(r.iloc[0]["y"])


@st.cache_data(ttl=3600, show_spinner=False)
def load_settori_trend() -> pd.DataFrame:
    return query(
        "SELECT * FROM mart_settori_trend WHERE country = 'IT' "
        "AND nace_r2 IN ('A','B-E','F','G-J','K-N','O-U','R-U') "
        "ORDER BY year, geo, gva_valore_mio DESC"
    )


@st.cache_data(ttl=3600, show_spinner=False)
def load_trend() -> pd.DataFrame:
    return query("SELECT * FROM mart_trend_integrato WHERE country = 'IT' ORDER BY pil_cagr_pct DESC")


@st.cache_data(ttl=3600, show_spinner=False)
def load_domanda() -> pd.DataFrame:
    return query("SELECT * FROM mart_domanda WHERE country = 'IT' ORDER BY year")


@st.cache_data(ttl=3600, show_spinner=False)
def load_domanda_all() -> pd.DataFrame:
    return query("SELECT * FROM mart_domanda ORDER BY year, country")


@st.cache_data(ttl=3600, show_spinner=False)
def load_riconciliazione() -> pd.DataFrame:
    return query("SELECT * FROM mart_riconciliazione ORDER BY year, geo")


@st.cache_data(ttl=3600, show_spinner=False)
def load_componenti() -> pd.DataFrame:
    return query("SELECT * FROM mart_pil_componenti ORDER BY year")


@st.cache_data(ttl=3600, show_spinner=False)
def load_imprese() -> pd.DataFrame:
    return query("SELECT * FROM mart_imprese_sintesi ORDER BY anno, nace_codice, size_class")


@st.cache_data(ttl=3600, show_spinner=False)
def load_convergenza() -> pd.DataFrame:
    return query("SELECT * FROM mart_convergenza ORDER BY year")
