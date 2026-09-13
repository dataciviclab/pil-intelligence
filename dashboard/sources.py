"""Data sources for PIL Intelligence dashboard.

Loads mart parquet files via lab_connectors DuckDB helpers.
Auto-detects local out/ or GCS.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

_MART_DIR = Path(__file__).parent.parent / "out" / "data" / "mart" / "pil_intelligence" / "2026"


@st.cache_resource(show_spinner=False)
def _con():
    import duckdb

    con = duckdb.connect(":memory:")
    for f in _MART_DIR.glob("*.parquet"):
        name = f.stem
        con.execute(f"CREATE TABLE {name} AS SELECT * FROM read_parquet('{f}')")
    return con


def query(sql: str) -> pd.DataFrame:
    return _con().execute(sql).fetchdf()


# --- Geo helpers ---

_MACRO_MAP = {
    "ITC": "Nord-Ovest",
    "ITH": "Nord-Est",
    "ITI": "Centro",
    "ITF": "Sud",
    "ITG": "Isole",
}


def macro_area(geo: str) -> str:
    """NUTS3 code → macro-area italiana."""
    return _MACRO_MAP.get(geo[:3], "Altro")


# --- Hub ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_hub() -> pd.DataFrame:
    return query("SELECT * FROM mart_hub WHERE country = 'IT' ORDER BY year, geo")


def latest_hub_year() -> int:
    r = query("SELECT MAX(year) AS y FROM mart_hub WHERE country = 'IT' AND pil_procapite_eur IS NOT NULL")
    return int(r.iloc[0]["y"])


@st.cache_data(ttl=3600, show_spinner=False)
def load_hub_anno(year: int) -> pd.DataFrame:
    return query(f"SELECT * FROM mart_hub WHERE country = 'IT' AND year = {year} ORDER BY pil_procapite_eur DESC")


# --- Settori ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_settori() -> pd.DataFrame:
    return query("SELECT * FROM mart_settori WHERE country = 'IT' ORDER BY year, geo, gva_valore_mio DESC")


def latest_settori_year() -> int:
    r = query("SELECT MAX(year) AS y FROM mart_settori WHERE country = 'IT' AND gva_valore_mio IS NOT NULL")
    return int(r.iloc[0]["y"])


@st.cache_data(ttl=3600, show_spinner=False)
def load_settori_anno(geo: str, year: int) -> pd.DataFrame:
    return query(f"SELECT * FROM mart_settori WHERE geo = '{geo}' AND year = {year} AND country = 'IT' ORDER BY gva_valore_mio DESC")


# --- Debito/Fisco ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_debito() -> pd.DataFrame:
    return query("SELECT * FROM mart_debito_fisco ORDER BY anno")


# --- Trend ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_trend() -> pd.DataFrame:
    return query("SELECT * FROM mart_trend_integrato WHERE country = 'IT' ORDER BY pil_cagr_pct DESC")


# --- Domanda ---

@st.cache_data(ttl=3600, show_spinner=False)
def load_domanda() -> pd.DataFrame:
    return query("SELECT * FROM mart_domanda WHERE country = 'IT' ORDER BY year")


@st.cache_data(ttl=3600, show_spinner=False)
def load_domanda_all() -> pd.DataFrame:
    return query("SELECT * FROM mart_domanda ORDER BY year, country")
