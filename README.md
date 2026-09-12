# PIL Intelligence

**Come sta realmente l'economia italiana? Le province convergono o divergono?**

Sistema di intelligence sul Prodotto Interno Lordo italiano: raccoglie i dati Eurostat (PIL, GVA, occupazione, produttività, turismo, criminalità, investimenti), le serie storiche OCPI e i dati di debito pubblico, li trasforma in 6 mart analitici e li rende interrogabili via dashboard Streamlit.

- **Fonte**: [Eurostat SDMX](https://ec.europa.eu/eurostat/web/sdmx-database), [OCPI](https://www.ocpi.it/)
- **Copertura**: 1861–2025 (debito), 2000–2023 (province), 1978–2026 (trimestrale)
- **Unità di analisi**: Province NUTS3 (107), Paesi (40), serie storica Italia
- **Output pubblico**: Dashboard Streamlit + parquet committati nel repo

## Cosa risponde

1. **Come sta l'economia italiana oggi?** → KPI nazionali: PIL pro-capite, GVA, occupati, debito/PIL
2. **Quali province crescono e quali restano indietro?** → CAGR, gap Nord-Sud, distribuzione PIL pro-capite
3. **Quali settori trainano l'economia?** → GVA per 14 settori NACE, evoluzione, confronto tra province
4. **Come si compone la domanda?** → Consumi, investimenti, export, import, saldo commerciale
5. **Quanto pesa il debito e cosa lo muove?** → Debito/PIL 1861–2025, spread i-g, saldo primario vs interessi
6. **Il PIL trimestrale conferma le tendenze?** → Variazione % trimestrale, ultimi 8 trimestri

## Mart

| Mart | Righe | Cosa |
|---|---|---|
| `mart_hub` | 32.500 | 107 province × 25 anni: PIL, GVA, occupazione, produttività, turismo, criminalità, GFCF |
| `mart_settori` | 37.800 | GVA per 14 settori NACE × province |
| `mart_debito_fisco` | 165 | Italia 1861–2025: debito/PIL, saldo primario, interessi, spread i-g |
| `mart_trend_integrato` | 1.300 | CAGR e delta multi-indicatore per provincia |
| `mart_domanda` | 2.040 | PIL per componenti della domanda (C+I+G+X-M), 40 paesi × 50 anni |
| `mart_trimestrale` | 776 | PIL trimestrale Italia, 1978–2026 |

## Dashboard

Dashboard Streamlit con 6 pagine:

| Pagina | Contenuto |
|---|---|
| **Panoramica** | KPI Italia, trend PIL pro-capite, composizione domanda, debito storico |
| **Territorio** | Treemap province, top/bottom, trend temporale |
| **Settori** | GVA per NACE, evoluzione, heatmap province × settori |
| **Domanda** | Composizione PIL, waterfall saldo commerciale, tabella, trimestrale |
| **Debito / Fisco** | Serie 1861–2025 con eventi annotati, spread i-g, saldo vs interessi |
| **Convergenza** | Box plot macro-area, CAGR, scatter convergenza, gap Nord-Sud |

```bash
cd dashboard && streamlit run app.py
```

## Come funziona

```
Eurostat SDMX + OCPI + Eurostat debito → toolkit (clean → mart) → parquet → dashboard
```

```bash
# Eseguire il compose (legge da GCS HTTPS)
toolkit run mart -c dataset.yml -y 2026

# Dashboard
cd dashboard && streamlit run app.py
```

**Compose** — il dataset è mart-only: non ha raw né clean propri. I 6 SQL leggono direttamente dai parquet clean/mart degli upstream su GCS HTTPS. Il toolkit risolve i path e produce i parquet in `out/data/mart/`.

**CI** — la workflow `.github/workflows/pipeline.yml` esegue `toolkit run mart` al 2° del mese (dopo eurostat/DPI) e commetta i parquet nel repo. La dashboard legge dai parquet committati.

**Dashboard** — legge i parquet da `out/data/mart/` (locale) o dal repo (produzione). Usa `lab_connectors` per formatters e DuckDB.

## Fonti

| Fonte | Cosa fornisce |
|---|---|
| Eurostat — `NAMA_10R_3GDP` | PIL pro-capite NUTS3 (EUR/hab) |
| Eurostat — `NAMA_10R_3GVA` | GVA per settore NACE × NUTS3 |
| Eurostat — `NAMA_10R_3EMPERS` | Occupati per settore × NUTS3 |
| Eurostat — `NAMA_10R_3NLP` | Produttività del lavoro NUTS3 |
| Eurostat — `NAMA_10R_2GFCF` | Formazione di capitale lordo NUTS2 |
| Eurostat — `NAMA_10_GDP` | PIL per componenti della domanda (40 paesi) |
| Eurostat — `NAMQ_10_GDP` | PIL trimestrale Italia |
| Eurostat — `TOUR_OCC_NIN2` | Presenze turistiche NUTS3 |
| Eurostat — `CRIM_GEN_REG` | Reati registrati NUTS3 |
| Eurostat — `GOV_10DD_EDPT1` | Debito/PIL (Maastricht) |
| OCPI | 26 serie storiche 1861–2025 (debito, PIL, i−g, saldo primario, interessi) |

Tutte le fonti sono pubbliche e verificabili.

## Perché fidarsi

- Fonti ufficiali Eurostat e OCPI
- Trasformazioni documentate in SQL, parquet committati nel repo
- Controlli automatici (min_rows su 4 tabelle)
- Standard condivisi del DataCivicLab (`.github`)

## Partecipa

- **Discussions** → domande civiche, interpretazioni, proposte di metriche
- **Issues** → bug, problemi tecnici, miglioramenti della pipeline

## Licenza

- **Dati**: CC BY 4.0
- **Codice**: MIT
