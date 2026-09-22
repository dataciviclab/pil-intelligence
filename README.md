# PIL Intelligence

**Come sta realmente l'economia italiana? Le province convergono o divergono?**

Sistema di intelligence sul Prodotto Interno Lordo italiano: raccoglie i dati Eurostat (PIL, GVA, occupazione, produttività, investimenti), le serie storiche OCPI e i dati di debito pubblico, li trasforma in 7 mart analitici e li rende interrogabili via dashboard Streamlit.

- **Fonte**: [Eurostat SDMX](https://ec.europa.eu/eurostat/web/sdmx-database), [OCPI](https://www.ocpi.it/)
- **Copertura**: 1861–2025 (debito), 2000–2024 (province), 1978–2026 (trimestrale)
- **Unità di analisi**: Province NUTS3 (107), Paesi (40), serie storica Italia
- **Output pubblico**: Dashboard Streamlit + parquet committati nel repo

## Cosa risponde

1. **Come sta l'economia italiana oggi?** → KPI: PIL pro-capite, produttività, tasso di investimento, occupazione
2. **Quali province crescono e quali restano indietro?** → CAGR PIL/GVA/occupazione, gap Nord-Sud
3. **Quali settori trainano l'economia?** → GVA per 7 macro-settori NACE, evoluzione, variazioni composizione
4. **Come si compone la domanda?** → Consumi, investimenti, export, import
5. **Quanto pesa il debito e cosa lo muove?** → Debito/PIL 1861–2025, spread i-g, saldo primario vs interessi

## Mart

| Mart | Righe | Cosa |
|---|---|---|
| `mart_hub` | 32.500 | 107 province × 25 anni: PIL, GVA, occupazione, produttività, GFCF, tasso investimento |
| `mart_settori` | 18.900 | GVA per 7 macro-settori NACE × province, share % normalizzate a 100% |
| `mart_settori_trend` | 18.900 | Variazioni share % (pp) e crescita GVA anno su anno per settore |
| `mart_trend_integrato` | 1.300 | CAGR e delta multi-indicatore per provincia (PIL, GVA, occupazione) |
| `mart_domanda` | 2.040 | PIL per componenti della domanda (C+I+G+X-M), 40 paesi × 50 anni |
| `mart_trimestrale` | 776 | PIL trimestrale Italia, 1978–2026 |
| `mart_debito_fisco` | 165 | Italia 1861–2025: debito/PIL, saldo primario, interessi, spread i-g |

## Data Dictionary

### mart_hub (per provincia NUTS3, per anno)

| Colonna | Tipo | Unità | Descrizione | Fonte |
|---|---|---|---|---|
| `year` | int | anno | Anno di riferimento | Eurostat |
| `geo` | str | codice NUTS3 | Codice provincia (es. ITC11 = Torino) | Eurostat |
| `geo_label_en` | str | — | Nome provincia in inglese | Eurostat |
| `nuts_level` | str | — | Livello NUTS (sempre "NUTS3") | Eurostat |
| `country` | str | codice ISO2 | Prefisso paese (sempre "IT") | Eurostat |
| `nuts_parent_code` | str | codice NUTS2 | Codice regione NUTS2 | Eurostat |
| `nuts_parent_label_en` | str | — | Nome regione in inglese | Eurostat |
| `popolazione` | int | persone | Popolazione residente (derivata: MIO_EUR / EUR_HAB) | Eurostat |
| `pil_procapite_eur` | double | EUR/hab | PIL pro-capite ai prezzi di mercato | Eurostat NAMA_10R_3GDP |
| `gva_totale_mio` | double | M EUR | Valore aggiunto lordo totale, prezzi correnti | Eurostat NAMA_10R_3GVA |
| `occupati_migliaia` | double | migliaia | Occupati totali (wstatus=EMP, nace=TOTAL) | Eurostat NAMA_10R_3EMPERS |
| `produttivita_lavoro_eur` | double | EUR/occupato | Produttività del lavoro nominale | Eurostat NAMA_10R_3NLP |
| `presenze_turistiche_migliaia` | double | migliaia | Presenze turistiche (I551-I553) | Eurostat TOUR_OCC_NIN2 |
| `reati_per_100k` | double | ogni 100k ab. | Reati registrati per 100.000 abitanti | Eurostat CRIM_GEN_REG |
| `gfcf_totale_mio` | double | M EUR | Formazione di capitale lordo, NUTS2, prezzi correnti | Eurostat NAMA_10R_2GFCF |
| `gva_procapite_eur` | double | EUR/hab | GVA pro-capite (derivato: GVA / popolazione) | Calcolato |
| `gva_per_lavoratore_eur` | double | EUR/occupato | GVA per occupato (derivato: GVA / occupati) | Calcolato |
| `tasso_occupazione_pct` | double | % | Tasso di occupazione (derivato: occupati / popolazione × 100) | Calcolato |
| `gfcf_su_va_pct` | double | % | Tasso di investimento (GFCF NUTS2 / somma GVA NUTS2 × 100) | Calcolato |

**Note metodologiche:**
- PIL pro-capite e popolazione sono a prezzi correnti (EUR_HAB)
- GFCF è a livello NUTS2, non NUTS3 — il ratio GFCF/VA è calcolato aggregando il VA delle province NUTS3 nella stessa regione NUTS2
- La popolazione è derivata da PIL totale / PIL pro-capite, non da un censimento diretto

### mart_settori (per provincia NUTS3, per anno, per macro-settore)

| Colonna | Tipo | Unità | Descrizione |
|---|---|---|---|
| `nace_r2` | str | codice NACE | Macro-settore: A, B-E, F, G-J, K-N, O-U, R-U |
| `nace_r2_label_en` | str | — | Descrizione settore |
| `gva_valore_mio` | double | M EUR | GVA del settore, prezzi correnti |
| `gva_totale_mio` | double | M EUR | GVA totale (TOTAL) della provincia |
| `share_pct` | double | % | Share normalizzata (somma = 100% per geo/year) |

**7 macro-settori NACE:**
- **A**: Agricoltura, silvicoltura, pesca
- **B-E**: Industria (senza costruzioni)
- **F**: Costruzioni
- **G-J**: Commercio, trasporti, alberghieri, informatica
- **K-N**: Finanza, immobiliare, professioni, amministrazione
- **O-U**: PA, difesa, istruzione, salute, servizi sociali, cultura
- **R-U**: Cultura, intrattenimento, altri servizi, organizzazioni internazionali

**Note:** Le share sono normalizzate per geo/year in modo che sommino esattamente a 100%, perché i macro-settori Eurostat a NUTS3 non sommano esattamente al TOTAL (divergenza strutturale del dato Eurostat).

### mart_trend_integrato (per provincia NUTS3, una riga)

| Colonna | Tipo | Descrizione |
|---|---|---|
| `pil_first_year` / `pil_last_year` | int | Primo/ultimo anno con dati PIL |
| `pil_first` / `pil_last` | double | PIL pro-capite primo/ultimo anno (EUR/HAB, prezzi correnti) |
| `pil_cagr_pct` | double | CAGR PIL pro-capite (%, periodo pil_first_year–pil_last_year) |
| `gva_first` / `gva_last` | double | GVA totale primo/ultimo anno (M EUR, prezzi correnti) |
| `gva_cagr_pct` | double | CAGR GVA totale |
| `emp_first` / `emp_last` | double | Occupati primo/ultimo anno (migliaia) |
| `emp_cagr_pct` | double | CAGR occupazione |
| `years_observed` | int | Numero di anni con dati disponibili |

**Attenzione:** I CAGR sono calcolati su valori nominali (prezzi correnti), non a prezzi costanti. Non misurano crescita reale.

### mart_settori_trend (per provincia NUTS3, per anno, per macro-settore)

| Colonna | Tipo | Unità | Descrizione |
|---|---|---|---|
| `share_pct` | double | % | Share normalizzata (vedi mart_settori) |
| `share_pct_prev` | double | % | Share anno precedente |
| `share_delta_pp` | double | pp | Variazione share in punti percentuali |
| `gva_yoy_pct` | double | % | Variazione GVA anno su anno |

## Dashboard

Dashboard Streamlit con 6 pagine:

| Pagina | Contenuto |
|---|---|
| **Panoramica** | 6 KPI (PIL pro-capite, produttività, tasso investimento, occupati, tasso occupazione, CAGR) + 4 contesto |
| **Territorio** | Treemap province, top/bottom, trend temporale |
| **Settori** | GVA per macro-settore, evoluzione, heatmap, variazioni composizione |
| **Domanda** | Composizione PIL, waterfall saldo commerciale, trimestrale |
| **Debito / Fisco** | Serie 1861–2025 con eventi annotati, spread i-g |
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

**Compose** — il dataset è mart-only: non ha raw né clean propri. I SQL leggono direttamente dai parquet clean/mart degli upstream su GCS HTTPS.

**CI** — la workflow `.github/workflows/pipeline.yml` esegue `toolkit run mart` al 2° del mese e commetta i parquet nel repo.

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
| OCPI | 26 serie storiche 1861–2025 (debito, PIL, i−g, saldo primario, interessi) |

## Perché fidarsi

- Fonti ufficiali Eurostat e OCPI
- Trasformazioni documentate in SQL, parquet committati nel repo
- Controlli automatici (min_rows su tabelle)
- Data dictionary esplicito con note metodologiche

## Licenza

- **Dati**: CC BY 4.0
- **Codice**: MIT
