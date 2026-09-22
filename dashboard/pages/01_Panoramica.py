"""01 — Panoramica: KPI Italia"""

import streamlit as st
import plotly.express as px

from sources import (
    load_hub, load_debito, load_domanda, query,
    latest_hub_year, _nat, _wavg, delta_pct, delta_pp,
)
from lab_connectors.formatters import fmt_eur, fmt_num

st.title("📊 Panoramica")

hub = load_hub()
debito = load_debito()
domanda = load_domanda()

latest = latest_hub_year()
prev = latest - 1

# --- Dati ---
pop = _nat(latest, "popolazione")
pop_prev = _nat(prev, "popolazione")
emp = _nat(latest, "occupati_migliaia")
emp_prev = _nat(prev, "occupati_migliaia")
gva = _nat(latest, "gva_totale_mio")
gva_prev = _nat(prev, "gva_totale_mio")
pil_procap = _wavg(latest, "pil_procapite_eur", "popolazione")
pil_procap_prev = _wavg(prev, "pil_procapite_eur", "popolazione")
prod = _wavg(latest, "produttivita_lavoro_eur", "popolazione")
prod_prev = _wavg(prev, "produttivita_lavoro_eur", "popolazione")
tasso_occ = _wavg(latest, "tasso_occupazione_pct", "popolazione")
tasso_occ_prev = _wavg(prev, "tasso_occupazione_pct", "popolazione")
gfcf_va = _wavg(latest, "gfcf_su_va_pct", "gva_totale_mio")
gfcf_va_prev = _wavg(prev, "gfcf_su_va_pct", "gva_totale_mio")

deb_latest = int(debito["anno"].max())
deb_curr = debito[debito["anno"] == deb_latest]
deb_prev = debito[debito["anno"] == deb_latest - 1]
d_curr = domanda[domanda["year"] == latest]

min_year = int(hub[hub["pil_procapite_eur"].notna()]["year"].min())
min_pil = _wavg(min_year, "pil_procapite_eur", "popolazione")
years = latest - min_year
cagr = ((pil_procap / min_pil) ** (1 / years) - 1) if years > 0 and min_pil and pil_procap else None

pil_yoy = None
if pil_procap and pil_procap_prev:
    pil_yoy = (pil_procap / pil_procap_prev - 1) * 100


# === KPI ===

st.caption("Economia")
c1, c2, c3 = st.columns(3)
c1.metric("PIL pro-capite", fmt_eur(pil_procap), delta_pct(pil_procap, pil_procap_prev),
          help=f"Anno {latest} · media ponderata per popolazione")
c2.metric("Produttività lavoro", fmt_eur(prod) if prod else "—",
          delta_pct(prod, prod_prev) if prod else None,
          help=f"Anno {latest} · VA / occupato, media ponderata")
c3.metric("Tasso di investimento", f"{gfcf_va:.1f}%" if gfcf_va else "—",
          delta_pct(gfcf_va, gfcf_va_prev) if gfcf_va else None,
          help=f"Anno {latest} · GFCF / VA, media ponderata")

st.caption("Lavoro e dinamica")
c4, c5, c6 = st.columns(3)
c4.metric("Occupati", f"{emp / 1000:.1f}M" if emp else "—",
          delta_pct(emp, emp_prev), help=f"Anno {latest} · totale occupati (milioni)")
c5.metric("Tasso di occupazione", f"{tasso_occ:.1f}%",
          delta_pct(tasso_occ, tasso_occ_prev),
          help=f"Anno {latest} · occupati / popolazione, media ponderata")
c6.metric("CAGR PIL pro-capite", f"{cagr * 100:.2f}%" if cagr else "—",
          f"{pil_yoy:+.1f}%" if pil_yoy else None,
          help=f"Crescita annua {min_year}–{latest}")

st.divider()

ctx1, ctx2, ctx3, ctx4 = st.columns(4)
ctx1.metric("GVA totale", fmt_eur(gva * 1e6, compact=True), delta_pct(gva, gva_prev))
if len(deb_curr) > 0:
    dp = deb_curr.iloc[0]["debito_pil_pct"]
    dp_p = deb_prev.iloc[0]["debito_pil_pct"] if len(deb_prev) > 0 else None
    ctx2.metric("Debito/PIL", f"{dp:.1f}%", delta_pp(dp, dp_p))
else:
    ctx2.metric("Debito/PIL", "—")
if len(d_curr) > 0:
    ctx3.metric("Export/PIL", f"{d_curr.iloc[0]['export_pct_pil']:.1f}%")
else:
    ctx3.metric("Export/PIL", "—")
ctx4.metric("Popolazione", fmt_num(pop), delta_pct(pop, pop_prev, threshold=0.05))


# === GRAFICI ===

st.divider()

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader(f"Evoluzione PIL pro-capite ({min_year}–{latest})")
    nat_trend = query("""
        SELECT year, SUM(pil_procapite_eur * popolazione) / SUM(popolazione) AS pil_medio
        FROM mart_hub WHERE country='IT' AND pil_procapite_eur IS NOT NULL AND popolazione IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    fig = px.line(nat_trend, x="year", y="pil_medio", markers=True,
                  labels={"pil_medio": "PIL pro-capite medio (€)", "year": "Anno"})
    fig.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

with col_right:
    st.subheader("Composizione domanda")
    if len(d_curr) > 0:
        row = d_curr.iloc[0]
        labels = ["Consumi famiglie", "Investimenti (GFCF)", "Export", "Import"]
        values = [row.get("consumi_finali", 0) or 0,
                  row.get("gfcf", 0) or 0,
                  row.get("export", 0) or 0,
                  row.get("import", 0) or 0]
        fig = px.pie(names=labels, values=values, hole=0.4)
        fig.update_layout(height=350, margin=dict(t=10), showlegend=True)
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Export/PIL: {row.get('export_pct_pil', 0) or 0:.1f}% · Anno {latest}")
    else:
        st.info("Dati domanda non disponibili")

st.divider()

st.subheader("Debito/PIL — serie storica")
d_deb = debito.copy()
fig = px.line(d_deb, x="anno", y="debito_pil_pct", markers=True,
              labels={"debito_pil_pct": "Debito/PIL (%)", "anno": "Anno"})
fig.update_layout(height=300, margin=dict(t=10))
st.plotly_chart(fig, width="stretch")
