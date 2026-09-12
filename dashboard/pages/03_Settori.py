"""03 — Settori: GVA per NACE"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sources import load_hub, load_settori, latest_settori_year

st.title("🏭 Settori")

hub = load_hub()
settori = load_settori()

# Solo anni con dati significativi
yc = settori[settori["gva_valore_mio"].notna()].groupby("year")["geo"].count()
years = sorted(yc[yc >= 100].index.tolist())
provinces = sorted(settori[settori["country"] == "IT"]["geo_label_en"].unique())

col_y, col_p = st.columns(2)
with col_y:
    year = st.select_slider("Anno", options=years, value=years[-1])
with col_p:
    province = st.selectbox("Provincia", provinces, index=provinces.index("Milano") if "Milano" in provinces else 0)

df = settori[(settori["year"] == year) & (settori["geo_label_en"] == province)].copy()
df = df[df["share_pct"].notna() & ~df["nace_r2"].str.contains("-", na=False)].sort_values("gva_valore_mio", ascending=False)

if len(df) == 0:
    st.warning("Nessun dato settoriale per questa provincia/anno")
    st.stop()


def _short_label(label: str, max_len: int = 30) -> str:
    """Trunca label NACE lunghe per leggibilità nei grafici."""
    if len(label) <= max_len:
        return label
    return label[:max_len - 1] + "…"


df["settore"] = df["nace_r2_label_en"].apply(_short_label)

# --- Bar chart GVA per settore ---
st.subheader(f"GVA per settore — {province} ({year})")
fig = px.bar(df, x="settore", y="gva_valore_mio",
             text="share_pct", text_auto=".1f",
             labels={"gva_valore_mio": "GVA (mln €)", "settore": "", "share_pct": "Share %"})
fig.update_layout(
    height=500, margin=dict(t=10, b=10),
    xaxis_tickangle=-35, xaxis_tickfont=dict(size=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# --- Trend settori top ---
st.subheader("Evoluzione settori")
top_n = st.slider("Mostra top N settori", 3, 10, 5)
top_settori = df.head(top_n)["nace_r2"].tolist()

trend = settori[
    (settori["geo_label_en"] == province) &
    (settori["nace_r2"].isin(top_settori)) &
    (settori["share_pct"].notna())
].copy()
trend["settore"] = trend["nace_r2_label_en"].apply(_short_label)

if len(trend) > 0:
    fig = px.line(trend, x="year", y="share_pct", color="settore",
                  labels={"share_pct": "Share % del GVA", "year": "Anno", "settore": ""})
    fig.update_layout(
        height=450, margin=dict(t=10, r=20),
        legend=dict(
            orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02,
            font=dict(size=10)
        )
    )
    fig.update_traces(line=dict(width=2.5))
    st.plotly_chart(fig, use_container_width=True)

# --- Heatmap province × settori ---
st.subheader("Confronto province (share %)")
all_provs = sorted(settori[(settori["year"] == year) & (settori["country"] == "IT")]["geo_label_en"].unique())
selected_provs = st.multiselect("Seleziona province", all_provs,
                                default=all_provs[:6] if len(all_provs) >= 6 else all_provs)

if selected_provs:
    heat = settori[
        (settori["year"] == year) &
        (settori["geo_label_en"].isin(selected_provs)) &
        (settori["share_pct"].notna()) &
        (~settori["nace_r2"].str.contains("-", na=False))
    ].copy()
    heat["settore"] = heat["nace_r2_label_en"].apply(lambda x: _short_label(x, 25))
    heat = heat.pivot_table(index="geo_label_en", columns="settore", values="share_pct", aggfunc="first")

    if not heat.empty:
        n_rows = len(heat)
        n_cols = len(heat.columns)

        # Build text matrix for display
        text_matrix = heat.round(1).astype(str).values.tolist()
        # Replace 'nan' with ''
        text_matrix = [[c if c != 'nan' else '' for c in row] for row in text_matrix]

        fig = go.Figure(data=go.Heatmap(
            z=heat.values,
            x=heat.columns.tolist(),
            y=heat.index.tolist(),
            text=text_matrix,
            texttemplate="%{text}",
            textfont={"size": 11},
            colorscale="YlOrRd",
            colorbar=dict(title="Share %"),
            hovertemplate="Provincia: %{y}<br>Settore: %{x}<br>Share: %{z:.1f}%<extra></extra>"
        ))
        fig.update_layout(
            height=max(400, n_rows * 50 + 120),
            margin=dict(t=20, l=10, r=10, b=80),
            xaxis=dict(
                tickangle=-45, tickfont=dict(size=9),
                side="bottom", title=""
            ),
            yaxis=dict(
                autorange="reversed", tickfont=dict(size=10),
                title=""
            ),
        )
        st.plotly_chart(fig, use_container_width=True)
