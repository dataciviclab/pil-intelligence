"""05 — Riconciliazione: il PIL si ricompone tra le fonti?"""

import pandas as pd
import plotly.express as px
import streamlit as st
from lab_connectors.formatters import fmt_eur
from sources import load_componenti, load_imprese, load_riconciliazione

st.title("🧮 Riconciliazione PIL")

st.caption(
    "Tre letture dello stesso PIL: identità di contabilità nazionale (spesa e reddito), "
    "Eurostat NUTS3 e ISTAT conti territoriali. Nota: Eurostat compila il NUTS3 italiano "
    "da ISTAT — lo scarto misura revisioni/metodologia, non misure indipendenti."
)

comp = load_componenti()
ric = load_riconciliazione()

# === Identità nazionale (reddito e spesa) ===

st.subheader("Italia — identità di contabilità nazionale")

c_last = comp.dropna(subset=["pil"]).iloc[-1]
latest = int(c_last["year"])
c_prev = comp[comp["year"] == latest - 1]

k1, k2, k3 = st.columns(3)
k1.metric("PIL (Italia)", fmt_eur(c_last["pil"] * 1e6, compact=True),
          help=f"Anno {latest} · Eurostat NAMA_10_GDP, prezzi correnti")
k2.metric("Scarto identità spesa", f"{c_last['spesa_scarto_mio']:,.0f} M€",
          help="PIL − (consumi + investimenti + export − import)")
k3.metric("Scarto identità reddito", f"{c_last['reddito_scarto_mio']:,.0f} M€",
          help="PIL − (redditi da lavoro + risultato gestione + imposte nette)")

col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Quote del reddito")
    fig = px.line(comp.dropna(subset=["pil"]), x="year",
                  y=["quota_lavoro_pct", "quota_capitale_pct"], markers=True,
                  labels={"value": "% del PIL", "year": "Anno", "variable": "Quota"})
    fig.update_layout(height=320, margin=dict(t=10),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02))
    st.plotly_chart(fig, width="stretch")

with col_b:
    st.subheader("Componenti della domanda")
    row = c_last
    labels = ["Consumi", "Investimenti", "Export", "Import"]
    values = [row["consumi_finali"], row["formazione_capitale_lorda"], row["export"], row["import"]]
    fig = px.pie(names=labels, values=values, hole=0.4)
    fig.update_layout(height=320, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

st.divider()

# === Provinciale: Eurostat vs ISTAT ===

st.subheader("Province — Eurostat vs ISTAT")

years = sorted(ric["year"].dropna().unique())
year = st.select_slider("Anno", options=years, value=years[-1])
df = ric[(ric["year"] == year) & ric["eurostat_vs_istat_pil_pct"].notna()].copy()

if len(df) == 0:
    st.info("Nessun dato di riconciliazione per l'anno selezionato")
else:
    scarto_medio = (df["eurostat_vs_istat_pil_pct"].abs() * df["istat_pil_mio"]).sum() / df["istat_pil_mio"].sum()
    identita_max = ric[ric["year"] == year]["istat_identita_scarto_mio"].abs().max()

    m1, m2, m3 = st.columns(3)
    m1.metric("Province", f"{len(df)}")
    m2.metric("Scarto medio ponderato", f"{scarto_medio:.2f}%",
              help="|PIL Eurostat − PIL ISTAT| / PIL, ponderato sul PIL provinciale")
    m3.metric("Identità ISTAT (VA+imposte)", f"{identita_max:,.0f} M€",
              help="Max |PIL − (VA + imposte nette)| tra le province: atteso ~0")

    st.subheader(f"Province con scarto maggiore — {year}")
    st.caption(
        "Lo scarto è ~costante entro la regione (correzione di calibrazione regionale): "
        "a livello nazionale le due fonti coincidono allo 0,005%."
    )
    top = df.reindex(df["eurostat_vs_istat_pil_pct"].abs().sort_values(ascending=False).index).head(15)
    fig = px.bar(top.sort_values("eurostat_vs_istat_pil_pct"), x="eurostat_vs_istat_pil_pct",
                 y="territorio_nome", orientation="h",
                 labels={"eurostat_vs_istat_pil_pct": "Scarto Eurostat−ISTAT (%)", "territorio_nome": ""})
    fig.update_layout(height=420, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

    with st.expander("Tabella completa"):
        show = df[["geo", "territorio_nome", "eurostat_gdp_mio", "istat_pil_mio",
                   "istat_va_mio", "istat_imposte_mio", "istat_identita_scarto_mio",
                   "eurostat_vs_istat_pil_pct"]].sort_values("istat_pil_mio", ascending=False)
        st.dataframe(show, width="stretch")

st.divider()

# === Imprese: identità reddito del valore aggiunto (SBS) ===

st.subheader("Imprese — il valore aggiunto si ricompone dai componenti")
st.caption(
    "ISTAT SBS, settori market: VA = salari + contributi + risultato lordo di gestione. "
    "Copre ~56% del GVA totale (non è il PIL)."
)

imp = load_imprese()
imp_year = int(imp["anno"].max())
imp_y = imp[imp["anno"] == imp_year]
tot = imp_y[(imp_y["nace_codice"] == "0010") & (imp_y["size_class"] == "Totale")]

if len(tot):
    t = tot.iloc[0]
    i1, i2, i3 = st.columns(3)
    i1.metric("VA imprese (SBS)", fmt_eur(t["va_mio"] * 1e6, compact=True),
              help=f"Anno {imp_year} · solo settori market")
    i2.metric("Scarto identità reddito", f"{imp_y['identita_scarto_mio'].abs().max():,.1f} M€",
              help="Max |VA − (salari + contributi + margini)| tra i settori")
    i3.metric("Quota lavoro", f"{t['quota_lavoro_pct']:.1f}%", help="(salari + contributi) / VA")

    by_size = imp_y[(imp_y["nace_codice"] == "0010") & (imp_y["size_class"] != "Totale")].copy()
    order = ["0-9", "10-19", "20-49", "50-249", "250+"]
    by_size["size_class"] = pd.Categorical(by_size["size_class"], order, ordered=True)
    by_size = by_size.sort_values("size_class")
    fig = px.bar(by_size, x="size_class", y=["quota_lavoro_pct", "quota_capitale_pct"],
                 barmode="group",
                 labels={"value": "% del VA", "size_class": "Classe di addetti", "variable": "Quota"})
    fig.update_layout(height=340, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")
