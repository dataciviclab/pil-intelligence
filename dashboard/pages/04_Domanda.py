"""04 — Domanda: composizione PIL per componenti"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sources import load_domanda, load_domanda_all
from lab_connectors.formatters import fmt_eur, fmt_num

st.title("📦 Composizione della domanda")

dom = load_domanda()

years = sorted(dom["year"].unique())
year = st.select_slider("Anno", options=years, value=years[-1])

row = dom[dom["year"] == year]
if len(row) == 0:
    st.warning("Dati non disponibili per questo anno")
    st.stop()
row = row.iloc[0]

# --- KPI ---
st.subheader(f"Italia — {year}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("PIL", fmt_eur(row["pil"] * 1e6, compact=True))
c2.metric("Consumi/PIL", f"{row.get('consumi_pct_pil', 0) or 0:.1f}%")
c3.metric("GFCF/PIL", f"{row.get('gfcf_pct_pil', 0) or 0:.1f}%")
c4.metric("Export/PIL", f"{row.get('export_pct_pil', 0) or 0:.1f}%")

st.divider()

# --- Composizione bar chart ---
st.subheader("Composizione")
col1, col2 = st.columns(2)

with col1:
    labels = ["Consumi finali", "GFCF", "Export"]
    values = [row.get("consumi_finali", 0) or 0,
              row.get("gfcf", 0) or 0,
              row.get("export", 0) or 0]
    text = [fmt_eur(v * 1e6, compact=True) for v in values]
    fig = px.bar(x=labels, y=values, text=text,
                 labels={"x": "", "y": "mln €"})
    fig.update_layout(height=350, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")

with col2:
    balance = (row.get("export", 0) or 0) - (row.get("import", 0) or 0)
    fig = go.Figure(go.Waterfall(
        name="Saldo commerciale", orientation="v",
        measure=["absolute", "relative", "total"],
        x=["Export", "Import", "Saldo"],
        y=[row.get("export", 0) or 0, -(row.get("import", 0) or 0), 0],
        text=[fmt_eur((row.get("export", 0) or 0) * 1e6, compact=True),
              f"-{fmt_eur((row.get('import', 0) or 0) * 1e6, compact=True)}",
              fmt_eur(balance * 1e6, compact=True)],
        textposition="outside",
    ))
    fig.update_layout(height=350, margin=dict(t=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")

# --- Confronto internazionale ---
COMPARE = {"IT": "Italia", "DE": "Germania", "FR": "Francia", "ES": "Spagna"}
dom_all = load_domanda_all()
comp = dom_all[(dom_all["country"].isin(COMPARE)) & (dom_all["year"] == year)].copy()
comp["paese"] = comp["country"].map(COMPARE)

if len(comp) > 1:
    st.subheader(f"Confronto EU4 — {year}")

    comp_sorted = comp.sort_values("export_pct_pil", ascending=True)
    fig = px.bar(comp_sorted, x="export_pct_pil", y="paese", orientation="h",
                 text="export_pct_pil", text_auto=".1f",
                 labels={"export_pct_pil": "Export/PIL %", "paese": ""},
                 color="paese", color_discrete_map={
                     "Italia": "#3b82f6", "Germania": "#22c55e",
                     "Francia": "#f59e0b", "Spagna": "#ef4444"
                 })
    fig.update_layout(height=250, margin=dict(t=10, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")

    show = comp[["paese", "pil", "consumi_pct_pil", "gfcf_pct_pil", "export_pct_pil",
                 "import_pct_pil", "saldo_commerciale_pct_pil"]].copy()
    show = show.rename(columns={
        "paese": "Paese", "pil": "PIL (mln€)",
        "consumi_pct_pil": "Consumi/PIL", "gfcf_pct_pil": "GFCF/PIL",
        "export_pct_pil": "Export/PIL", "import_pct_pil": "Import/PIL",
        "saldo_commerciale_pct_pil": "Saldo comm."
    })
    show["PIL (mln€)"] = show["PIL (mln€)"].map(lambda v: fmt_eur(v * 1e6, compact=True))
    for c in ["Consumi/PIL", "GFCF/PIL", "Export/PIL", "Import/PIL", "Saldo comm."]:
        show[c] = show[c].map(lambda v: f"{v:.1f}%" if v == v else "—")
    st.dataframe(show, width="stretch", hide_index=True)

st.divider()

# --- Trend storico ---
st.subheader("Evoluzione nel tempo")
d = dom[dom["year"] >= 1990].copy()

col_a, col_b = st.columns(2)
with col_a:
    fig = px.line(d, x="year", y="consumi_pct_pil", labels={"consumi_pct_pil": "Consumi/PIL %", "year": ""})
    fig.add_scatter(x=d["year"], y=d["gfcf_pct_pil"], mode="lines", name="GFCF/PIL %")
    fig.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

with col_b:
    fig = px.line(d, x="year", y="export_pct_pil", labels={"export_pct_pil": "Export/PIL %", "year": ""})
    fig.add_scatter(x=d["year"], y=d["import_pct_pil"], mode="lines", name="Import/PIL %")
    fig.update_layout(height=350, margin=dict(t=10))
    st.plotly_chart(fig, width="stretch")

# --- Tabella ultimi 10 anni ---
st.subheader("Tabella riepilogativa")
show = d[d["year"] >= year - 10].copy()
cols = ["year", "pil", "consumi_finali", "gfcf", "export", "import"]
show = show[[c for c in cols if c in show.columns]]
show = show.rename(columns={"year": "Anno", "pil": "PIL (mln€)", "consumi_finali": "Consumi",
                             "gfcf": "GFCF", "export": "Export", "import": "Import"})
for c in show.columns[1:]:
    show[c] = show[c].map(lambda v: fmt_eur(v * 1e6, compact=True) if v == v else "—")
st.dataframe(show, width="stretch", hide_index=True)

# --- Vista trimestrale ---
st.divider()
st.subheader("📈 Ultimi trimestri — variazione % su trimestre precedente")

from sources import query
qt = query("SELECT * FROM mart_trimestrale ORDER BY year DESC, quarter DESC, na_item")

if len(qt) > 0:
    # Pivot: riga = trimestre, colonna = indicatore
    pivot = qt.pivot_table(index=["year", "quarter"], columns="na_item_label_en", values="value", aggfunc="first")
    pivot = pivot.reset_index(drop=False)
    # Dedup columns
    pivot = pivot.loc[:, ~pivot.columns.duplicated()]
    # Rename
    col_map = {
        "Gross domestic product at market prices": "PIL",
        "Final consumption expenditure": "Consumi",
        "Exports of goods and services": "Export",
        "Imports of goods and services": "Import",
    }
    pivot = pivot.rename(columns=col_map)
    pivot["trimestre"] = pivot["year"].astype(str) + " " + pivot["quarter"]
    show_cols = ["trimestre"] + [v for v in col_map.values() if v in pivot.columns]
    pivot = pivot[show_cols].sort_values("trimestre", ascending=False).head(8)

    st.dataframe(pivot, width="stretch", hide_index=True)

    # Mini chart PIL trimestrale
    fig = px.bar(pivot, x="trimestre", y="PIL", text="PIL",
                 labels={"PIL": "Var % PIL", "trimestre": ""},
                 color="PIL", color_continuous_scale=["#ef4444", "#22c55e"],
                 color_continuous_midpoint=0)
    fig.update_layout(height=280, margin=dict(t=10), showlegend=False,
                      coloraxis_showscale=False)
    fig.update_traces(texttemplate="%{text:+.1f}%", textposition="outside")
    st.plotly_chart(fig, width="stretch")
else:
    st.info("Dati trimestrali non disponibili")
