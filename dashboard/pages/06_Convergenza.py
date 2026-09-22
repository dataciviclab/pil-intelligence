"""06 — Convergenza: gap Nord-Sud e distribuzione"""

import streamlit as st
import plotly.express as px
import pandas as pd

from sources import load_hub, load_trend, macro_area

st.title("📐 Convergenza territoriale")

hub = load_hub()
trend = load_trend()

hub["macro_area"] = hub["geo"].apply(macro_area)
trend["macro_area"] = trend["geo"].apply(macro_area)

years = sorted(hub[hub["pil_procapite_eur"].notna()]["year"].unique())
year = st.select_slider("Anno", options=years, value=years[-1])

df = hub[(hub["year"] == year) & hub["pil_procapite_eur"].notna()].copy()

# --- Distribuzione ---
st.subheader(f"Distribuzione PIL pro-capite — {year}")
fig = px.box(df, x="macro_area", y="pil_procapite_eur", color="macro_area",
             labels={"pil_procapite_eur": "PIL pro-capite (€)", "macro_area": "Macro-area"},
             color_discrete_map={"Nord-Ovest": "#3b82f6", "Nord-Est": "#6366f1",
                                 "Centro": "#f59e0b", "Sud": "#ef4444", "Isole": "#f97316"})
fig.update_layout(height=400, margin=dict(t=10), showlegend=False)
st.plotly_chart(fig, width="stretch")

# --- CAGR per macro-area ---
_first_y = int(trend["pil_first_year"].min())
_last_y = int(trend["pil_last_year"].max())
st.subheader(f"CAGR PIL pro-capite per macro-area ({_first_y}–{_last_y})")
area_cagr = trend.groupby("macro_area").agg(
    cagr_medio=("pil_cagr_pct", "mean"), n=("geo", "count")).reset_index().sort_values("cagr_medio", ascending=True)

fig = px.bar(area_cagr, x="cagr_medio", y="macro_area", orientation="h",
             text="cagr_medio", text_auto=".2f",
             labels={"cagr_medio": "CAGR medio (%)", "macro_area": ""},
             color="macro_area",
             color_discrete_map={"Nord-Ovest": "#3b82f6", "Nord-Est": "#6366f1",
                                 "Centro": "#f59e0b", "Sud": "#ef4444", "Isole": "#f97316"})
fig.update_layout(height=300, margin=dict(t=10), showlegend=False)
st.plotly_chart(fig, width="stretch")

# --- Scatter convergenza ---
st.subheader("Convergenza: PIL iniziale vs velocità di crescita")
t = trend[trend["pil_first"].notna() & trend["pil_cagr_pct"].notna()].copy()
fig = px.scatter(t, x="pil_first", y="pil_cagr_pct", color="macro_area",
                 size="years_observed", hover_name="geo_label_en",
                 labels={"pil_first": f"PIL pro-capite {_first_y} (€)",
                         "pil_cagr_pct": f"CAGR {_first_y}-{_last_y} (%)"})
fig.update_layout(height=450, margin=dict(t=10))
st.plotly_chart(fig, width="stretch")
corr = t["pil_first"].corr(t["pil_cagr_pct"])
st.caption(f"Correlazione PIL iniziale × CAGR: {corr:.3f} ({'convergenza' if corr < 0 else 'divergenza'})")

# --- Gap timeline ---
st.subheader("Evoluzione del gap Nord-Sud")
gap = hub[hub["macro_area"].isin(["Nord-Ovest", "Nord-Est", "Sud", "Isole"])].copy()
if len(gap) > 0:
    avg = gap.groupby(["year", "macro_area"])["pil_procapite_eur"].mean().reset_index()
    fig = px.line(avg, x="year", y="pil_procapite_eur", color="macro_area",
                  labels={"pil_procapite_eur": "PIL pro-capite medio (€)", "year": "Anno"})
    fig.update_layout(height=400, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

# --- Tabella CAGR province ---
st.subheader("Classifica CAGR province")
show = trend[["geo_label_en", "macro_area", "pil_cagr_pct", "gva_cagr_pct", "emp_cagr_pct"]].copy()
show = show.rename(columns={"geo_label_en": "Provincia", "macro_area": "Area",
                             "pil_cagr_pct": "CAGR PIL %", "gva_cagr_pct": "CAGR GVA %",
                             "emp_cagr_pct": "CAGR Occupazione %"})
st.dataframe(show, width="stretch", hide_index=True, height=400)
