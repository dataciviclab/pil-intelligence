"""01 — Panoramica: KPI Italia"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sources import load_hub, load_debito, load_domanda, query, latest_hub_year
from lab_connectors.formatters import fmt_eur, fmt_num, fmt_pct

st.title("📊 Panoramica")

hub = load_hub()
debito = load_debito()
domanda = load_domanda()

# Ultimo anno con dati PIL
latest = latest_hub_year()
prev = latest - 1

# --- Aggregati nazionali da hub (somma province) ---
def _nat(year, col):
    r = query(f"SELECT SUM({col}) AS v FROM mart_hub WHERE country='IT' AND year={year} AND {col} IS NOT NULL")
    return float(r.iloc[0]["v"]) if len(r) > 0 and r.iloc[0]["v"] is not None else None

emp = _nat(latest, "occupati_migliaia")
emp_prev = _nat(prev, "occupati_migliaia")
gva = _nat(latest, "gva_totale_mio")
gva_prev = _nat(prev, "gva_totale_mio")

# PIL pro-capite medio (media ponderata non disponibile, usiamo la media)
pil_procap = query(f"SELECT AVG(pil_procapite_eur) AS v FROM mart_hub WHERE country='IT' AND year={latest} AND pil_procapite_eur IS NOT NULL").iloc[0]["v"]
pil_procap_prev = query(f"SELECT AVG(pil_procapite_eur) AS v FROM mart_hub WHERE country='IT' AND year={prev} AND pil_procapite_eur IS NOT NULL").iloc[0]["v"]

# Debito — ultimo anno disponibile (indipendente dal PIL)
deb_latest = int(debito["anno"].max())
deb_curr = debito[debito["anno"] == deb_latest]
deb_prev = debito[debito["anno"] == deb_latest - 1]

# Domanda
d_curr = domanda[domanda["year"] == latest]
d_prev = domanda[domanda["year"] == prev]

# --- KPI Cards ---
c1, c2, c3 = st.columns(3)

def _delta(curr_v, prev_v):
    if curr_v is None or prev_v is None or prev_v == 0:
        return None
    return f"{(curr_v/prev_v - 1)*100:+.1f}%"

c1.metric("PIL pro-capite (media)", fmt_eur(pil_procap), _delta(pil_procap, pil_procap_prev), help=f"Anno {latest} · media province")
c2.metric("GVA totale", fmt_eur(gva * 1e6, compact=True), _delta(gva, gva_prev), help=f"Anno {latest} · somma province")
c3.metric("Occupati", f"{fmt_num(emp)}k", _delta(emp, emp_prev), help=f"Anno {latest} · somma province")

c4, c5, c6 = st.columns(3)

if len(deb_curr) > 0:
    deb_y = int(deb_curr.iloc[0]["anno"])
    dp = deb_curr.iloc[0]["debito_pil_pct"]
    dp_d = f"{dp - deb_prev.iloc[0]['debito_pil_pct']:+.1f}pp" if len(deb_prev) > 0 else None
    c4.metric("Debito/PIL", f"{dp:.1f}%", dp_d, help=f"Anno {deb_y} · dati Eurostat")
else:
    c4.metric("Debito/PIL", "—")

if len(d_curr) > 0:
    dom_y = int(d_curr.iloc[0]["year"])
    c5.metric("Export/PIL", f"{d_curr.iloc[0]['export_pct_pil']:.1f}%",
              help=f"Anno {dom_y} · dati Eurostat")
else:
    c5.metric("Export/PIL", "—")

# CAGR
min_year = int(hub[hub["pil_procapite_eur"].notna()]["year"].min())
min_pil = query(f"SELECT AVG(pil_procapite_eur) AS v FROM mart_hub WHERE country='IT' AND year={min_year} AND pil_procapite_eur IS NOT NULL").iloc[0]["v"]
years = latest - min_year
if years > 0 and min_pil and pil_procap:
    cagr_val = (pil_procap / min_pil) ** (1 / years) - 1
    c6.metric("CAGR PIL", f"{cagr_val*100:.2f}%")
else:
    c6.metric("CAGR PIL", "—")

st.divider()

# --- Sparkline PIL (media nazionale per anno) ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader(f"Evoluzione PIL pro-capite ({min_year}–{latest})")
    nat_trend = query(f"""
        SELECT year, AVG(pil_procapite_eur) AS pil_medio
        FROM mart_hub WHERE country='IT' AND pil_procapite_eur IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    fig = px.line(nat_trend, x="year", y="pil_medio", markers=True,
                  labels={"pil_medio": "PIL pro-capite medio (€)", "year": "Anno"})
    fig.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Composizione consumi/export/import")
    if len(d_curr) > 0:
        row = d_curr.iloc[0]
        labels = ["Consumi", "GFCF", "Export", "Import"]
        values = [row.get("consumi_finali", 0) or 0,
                  row.get("gfcf", 0) or 0,
                  row.get("export", 0) or 0,
                  row.get("import", 0) or 0]
        fig = px.pie(names=labels, values=values, hole=0.4)
        fig.update_layout(height=350, margin=dict(t=10), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Percentuali sul totale dei 4 flussi. Export/PIL: {:.1f}%".format(
            row.get("export_pct_pil", 0) or 0))
    else:
        st.info("Dati domanda non disponibili")

st.divider()

# --- Debito/PIL storico ---
st.subheader("Debito/PIL — serie storica")
d_deb = debito.copy()
fig = px.line(d_deb, x="anno", y="debito_pil_pct", markers=True,
              labels={"debito_pil_pct": "Debito/PIL (%)", "anno": "Anno"})
fig.update_layout(height=300, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)
