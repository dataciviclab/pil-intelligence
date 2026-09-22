"""03 — Settori: GVA per macro-settore"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sources import load_settori, load_settori_trend

st.title("🏭 Settori")

settori = load_settori()

yc = settori[settori["gva_valore_mio"].notna()].groupby("year")["geo"].count()
years = sorted(yc[yc >= 100].index.tolist())
provinces = sorted(settori["geo_label_en"].unique())

col_y, col_p = st.columns(2)
with col_y:
    year = st.select_slider("Anno", options=years, value=years[-1])
with col_p:
    province = st.selectbox("Provincia", provinces, index=provinces.index("Milano") if "Milano" in provinces else 0)


def _short(label, n=30):
    return label if len(label) <= n else label[:n - 1] + "…"


df = settori[(settori["year"] == year) & (settori["geo_label_en"] == province)].copy()
df = df[df["share_pct"].notna()].sort_values("gva_valore_mio", ascending=False)

if len(df) == 0:
    st.warning("Nessun dato settoriale per questa provincia/anno")
    st.stop()

df["settore"] = df["nace_r2_label_en"].apply(_short)

# --- Bar chart ---
st.subheader(f"GVA per settore — {province} ({year})")
fig = px.bar(df, x="settore", y="gva_valore_mio",
             text="share_pct", text_auto=".1f",
             labels={"gva_valore_mio": "GVA (mln €)", "settore": "", "share_pct": "Share %"})
fig.update_layout(height=500, margin=dict(t=10, b=10), xaxis_tickangle=-35, xaxis_tickfont=dict(size=10))
st.plotly_chart(fig, width="stretch")

# --- Trend share ---
st.subheader("Evoluzione settori")
top_n = st.slider("Mostra top N settori", 3, 7, 5)
top_settori = df.head(top_n)["nace_r2"].tolist()

trend = settori[(settori["geo_label_en"] == province) & (settori["nace_r2"].isin(top_settori))].copy()
trend["settore"] = trend["nace_r2_label_en"].apply(_short)

if len(trend) > 0:
    fig = px.line(trend, x="year", y="share_pct", color="settore",
                  labels={"share_pct": "Share % del GVA", "year": "Anno", "settore": ""})
    fig.update_layout(height=450, margin=dict(t=10, r=20),
                      legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02, font=dict(size=10)))
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, width="stretch")

# --- Heatmap ---
st.subheader("Confronto province (share %)")
all_provs = sorted(settori[settori["year"] == year]["geo_label_en"].unique())
selected = st.multiselect("Seleziona province", all_provs,
                          default=all_provs[:6] if len(all_provs) >= 6 else all_provs)

if selected:
    heat = settori[(settori["year"] == year) & (settori["geo_label_en"].isin(selected)) & settori["share_pct"].notna()].copy()
    heat["settore"] = heat["nace_r2_label_en"].apply(lambda x: _short(x, 25))
    heat = heat.pivot_table(index="geo_label_en", columns="settore", values="share_pct", aggfunc="first")

    if not heat.empty:
        text = heat.round(1).astype(str).values.tolist()
        text = [[c if c != "nan" else "" for c in row] for row in text]
        fig = go.Figure(data=go.Heatmap(
            z=heat.values, x=heat.columns.tolist(), y=heat.index.tolist(),
            text=text, texttemplate="%{text}", textfont={"size": 11},
            colorscale="YlOrRd", colorbar=dict(title="Share %"),
            hovertemplate="Provincia: %{y}<br>Settore: %{x}<br>Share: %{z:.1f}%<extra></extra>"))
        fig.update_layout(
            height=max(400, len(heat) * 50 + 120),
            margin=dict(t=20, l=10, r=10, b=80),
            xaxis=dict(tickangle=-45, tickfont=dict(size=9), side="bottom", title=""),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10), title=""))
        st.plotly_chart(fig, width="stretch")

# --- Variazioni ---
st.divider()
st.subheader("Variazioni composizione settoriale")

st_yr = load_settori_trend()
st_yr = st_yr[(st_yr["geo_label_en"] == province) & st_yr["share_pct"].notna()]

if len(st_yr) > 0:
    last_yr = int(st_yr["year"].max())

    col_chart, col_table = st.columns([2, 1])

    with col_chart:
        st.caption(f"Variazione share % ultimo anno — {province}")
        df_bar = st_yr[st_yr["year"] == last_yr].copy()
        df_bar["settore"] = df_bar["nace_r2_label_en"].apply(_short)
        df_bar = df_bar[df_bar["share_delta_pp"].notna()].sort_values("share_delta_pp")
        fig = px.bar(df_bar, x="share_delta_pp", y="settore", orientation="h",
                     text="share_delta_pp", text_auto="+.2f",
                     labels={"share_delta_pp": "Variazione share (pp)", "settore": ""},
                     color="share_delta_pp",
                     color_continuous_scale=["#ef4444", "#e5e7eb", "#22c55e"],
                     color_continuous_midpoint=0)
        fig.update_layout(height=400, margin=dict(t=10, r=20), coloraxis_showscale=False)
        fig.update_traces(texttemplate="%{text:.2f}pp", textposition="outside")
        st.plotly_chart(fig, width="stretch")

    with col_table:
        st.caption(f"Ultimo anno ({last_yr}) — variazione vs anno precedente")
        tab = st_yr[st_yr["year"] == last_yr][["nace_r2_label_en", "share_pct", "share_delta_pp", "gva_yoy_pct"]].copy()
        tab = tab.rename(columns={"nace_r2_label_en": "Settore", "share_pct": "Share %",
                                  "share_delta_pp": "Δ Share pp", "gva_yoy_pct": "Δ GVA %"})
        tab["Settore"] = tab["Settore"].apply(_short)
        tab = tab.sort_values("Share %", ascending=False)
        st.dataframe(tab, width="stretch", hide_index=True, height=400)
