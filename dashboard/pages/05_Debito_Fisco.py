"""05 — Debito / Fisco: serie storica Italia"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sources import load_debito
from lab_connectors.formatters import fmt_eur, fmt_pct

st.title("💰 Debito / Fisco")

deb = load_debito()
if len(deb) == 0:
    st.warning("Nessun dato debito disponibile")
    st.stop()

# Ultimo anno
latest = deb["anno"].max()
curr = deb[deb["anno"] == latest].iloc[0]

# --- KPI ---
c1, c2, c3, c4 = st.columns(4)
c1.metric("Debito/PIL", f"{curr['debito_pil_pct']:.1f}%")
c2.metric("Stock debito", fmt_eur(curr["stock_mln_eur"] * 1e6, compact=True))
c3.metric("Saldo primario", f"{curr.get('saldo_primario_pct', 0):+.2f}% PIL")
c4.metric("Spesa interessi", f"{curr.get('interessi_pct_pil', 0):.1f}% PIL")

st.divider()

# --- Debito/PIL storico con eventi ---
st.subheader("Debito/PIL — serie storica (1861–{})".format(latest))

events = [
    (1914, "WWI"),
    (1940, "WWII"),
    (1980, "Duka"),
    (1992, "Crisi Lira"),
    (2008, "GFC"),
    (2011, "Crisi Euro"),
    (2020, "COVID"),
]

fig = px.line(deb, x="anno", y="debito_pil_pct", markers=True,
              labels={"debito_pil_pct": "Debito/PIL (%)", "anno": "Anno"})
for ev_year, ev_label in events:
    fig.add_vline(x=ev_year, line_dash="dot", line_color="gray", opacity=0.5)
    fig.add_annotation(x=ev_year, y=deb["debito_pil_pct"].max() * 0.95,
                       text=ev_label, showarrow=False, textangle=-90,
                       font=dict(size=9, color="gray"))
fig.update_layout(height=400, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)

# --- Spread i-g ---
st.subheader("Spread i-g vs crescita PIL")
if "spread_i_g" in deb.columns:
    d = deb[deb["anno"] >= 1980].copy()
    fig = px.line(d, x="anno", y="spread_i_g",
                  labels={"spread_i_g": "Spread i-g (pp)", "anno": "Anno"})
    fig.add_hline(y=0, line_color="red", line_dash="dash", opacity=0.5)
    fig.update_layout(height=300, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

# --- Composizione: saldo + interessi ---
st.subheader("Saldo primario vs interessi")
d2 = deb[deb["anno"] >= 1990].copy()
if "saldo_primario_pct" in d2.columns and "interessi_pct_pil" in d2.columns:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d2["anno"], y=d2["saldo_primario_pct"], name="Saldo primario",
                         marker_color="steelblue"))
    fig.add_trace(go.Scatter(x=d2["anno"], y=d2["interessi_pct_pil"], name="Interessi",
                             mode="lines+markers", line=dict(color="indianred", width=2)))
    fig.update_layout(barmode="relative", height=350, margin=dict(t=10),
                      yaxis_title="% PIL", xaxis_title="Anno")
    st.plotly_chart(fig, use_container_width=True)

# --- Tabella ultimi 20 anni ---
st.subheader("Tabella")
show = deb[deb["anno"] >= latest - 20][["anno", "pil_nominale_mln", "debito_pil_pct",
                                         "saldo_primario_pct", "interessi_pct_pil", "spread_i_g"]].copy()
show = show.rename(columns={"anno": "Anno", "pil_nominale_mln": "PIL (mln€)",
                             "debito_pil_pct": "Debito/PIL %", "saldo_primario_pct": "Saldo prim %",
                             "interessi_pct_pil": "Interessi %", "spread_i_g": "Spread i-g"})
st.dataframe(show, use_container_width=True, hide_index=True)
