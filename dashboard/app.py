#!/usr/bin/env python3
"""PIL Intelligence · Dashboard Streamlit"""

import streamlit as st

st.set_page_config(
    page_title="PIL Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

from lab_connectors.branding import apply_branding

apply_branding(repo_name="pil-intelligence", repo_url="https://github.com/dataciviclab/pil-intelligence")

pages = {
    "": [
        st.Page("pages/01_Panoramica.py", title="Panoramica", icon="📊", default=True),
    ],
    "Analisi": [
        st.Page("pages/02_Territorio.py", title="Territorio", icon="🗺️"),
        st.Page("pages/03_Settori.py", title="Settori", icon="🏭"),
        st.Page("pages/04_Domanda.py", title="Domanda", icon="📦"),
        st.Page("pages/05_Debito_Fisco.py", title="Debito / Fisco", icon="💰"),
        st.Page("pages/06_Convergenza.py", title="Convergenza", icon="📐"),
    ],
}

pg = st.navigation(pages, position="sidebar")
pg.run()
