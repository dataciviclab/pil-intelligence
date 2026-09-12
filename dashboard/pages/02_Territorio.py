"""02 — Territorio: mappa e treemap province"""

import streamlit as st
import plotly.express as px

from sources import load_hub, load_hub_anno, latest_hub_year, macro_area
from lab_connectors.formatters import fmt_eur, fmt_num

st.title("🗺️ Territorio")

hub = load_hub()
latest = latest_hub_year()
# Solo anni con almeno 50 province con dati (escludi anni con tutti NULL)
year_counts = hub[hub["pil_procapite_eur"].notna()].groupby("year")["geo"].count()
years = sorted(year_counts[year_counts >= 50].index.tolist())

col_y, col_ind = st.columns(2)
with col_y:
    year = st.select_slider("Anno", options=years, value=years[-1])
with col_ind:
    indicator = st.selectbox("Indicatore", [
        "pil_procapite_eur", "gva_totale_mio", "occupati_migliaia",
        "produttivita_lavoro_eur", "reati_per_100k", "gfcf_totale_mio"
    ], format_func=lambda x: {
        "pil_procapite_eur": "PIL pro-capite (€)",
        "gva_totale_mio": "GVA totale (mln €)",
        "occupati_migliaia": "Occupati (migliaia)",
        "produttivita_lavoro_eur": "Produttività lavoro (€)",
        "reati_per_100k": "Reati / 100k ab.",
        "gfcf_totale_mio": "GFCF (mln €)",
    }[x])

df = load_hub_anno(year)
df = df[df[indicator].notna()].copy()

if len(df) == 0:
    st.warning("Nessun dato disponibile per questa combinazione")
    st.stop()

df["macro_area"] = df["geo"].apply(macro_area)

# --- Treemap ---
st.subheader(f"Province per {indicator} — {year}")
fig = px.treemap(
    df, path=["macro_area", "geo_label_en"], values=indicator,
    color=indicator, color_continuous_scale="Blues",
    hover_data={indicator: ":,.0f", "geo": False, "macro_area": False}
)
fig.update_layout(height=500, margin=dict(t=10))
st.plotly_chart(fig, use_container_width=True)

# --- Top/Bottom table ---
st.subheader("Classifica province")
c1, c2 = st.columns(2)

def _fmt_val(v, ind):
    if v != v:  # NaN
        return "—"
    if ind == "reati_per_100k":
        return f"{v:,.1f}"
    return fmt_eur(v) if "eur" in ind or "mio" in ind else fmt_num(v)

with c1:
    st.markdown("**Top 10**")
    top = df.head(10)[["geo_label_en", "macro_area", indicator]].copy()
    top["indicatore"] = top[indicator].map(lambda v: _fmt_val(v, indicator))
    st.dataframe(
        top[["geo_label_en", "macro_area", "indicatore"]].rename(columns={
            "geo_label_en": "Provincia", "macro_area": "Area"
        }),
        use_container_width=True, hide_index=True
    )
with c2:
    st.markdown("**Bottom 10**")
    bot = df.tail(10)[["geo_label_en", "macro_area", indicator]].copy()
    bot["indicatore"] = bot[indicator].map(lambda v: _fmt_val(v, indicator))
    st.dataframe(
        bot[["geo_label_en", "macro_area", "indicatore"]].rename(columns={
            "geo_label_en": "Provincia", "macro_area": "Area"
        }),
        use_container_width=True, hide_index=True
    )

# --- Trend selezionabile ---
st.subheader("Trend temporale")
selected = st.multiselect("Seleziona province", df["geo_label_en"].tolist(),
                          default=df.head(3)["geo_label_en"].tolist())
if selected:
    trend = hub[hub["geo_label_en"].isin(selected)]
    fig = px.line(trend, x="year", y=indicator, color="geo_label_en",
                  labels={indicator: indicator, "year": "Anno", "geo_label_en": "Provincia"})
    fig.update_layout(height=400, margin=dict(t=10))
    st.plotly_chart(fig, use_container_width=True)
