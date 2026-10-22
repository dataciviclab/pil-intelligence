# PIL Intelligence

**Il PIL italiano si ricompone tra le fonti? Quanto divergono Eurostat, ISTAT e la contabilità nazionale?**

Sistema di intelligence sul Prodotto Interno Lordo italiano: compone indicatori
Eurostat a livello provinciale (PIL, GVA, occupazione, produttività, investimenti),
e **riconcilia** il PIL tra fonti indipendenti — Eurostat NUTS3, ISTAT conti
territoriali e identità di contabilità nazionale (produzione, reddito, spesa).

- **Fonti**: [Eurostat SDMX](https://ec.europa.eu/eurostat/web/sdmx-database), [ISTAT conti territoriali](https://www.istat.it/)
- **Copertura**: province 2000–2023 (ISTAT/Eurostat), domanda nazionale 1975–2025, trimestrale 1978–2026
- **Unità di analisi**: Province NUTS3 (107), Paesi (41), Italia (serie storica)
- **Output pubblico**: dashboard Streamlit + mart parquet pubblicati su GCS

## Cosa risponde

1. **Come sta l'economia italiana oggi?** → PIL pro-capite, produttività, tasso di investimento, occupazione
2. **Quali province crescono e quali restano indietro?** → CAGR PIL/GVA/occupazione, gap Nord-Sud
3. **Quali settori trainano l'economia?** → GVA per 7 macro-settori NACE, evoluzione, composizione
4. **Come si compone la domanda?** → Consumi, investimenti, export, import (nazionale, 41 paesi)
5. **Il PIL si ricompone?** → Eurostat vs ISTAT vs identità contabile, con scarti misurati

## Riconciliazione del PIL

Il PIL non è "ricostruito" da microdati: è un aggregato ufficiale che il Lab legge e
**verifica** incrociando fonti indipendenti. A ogni livello si può ricomporre il PIL
dai suoi componenti pubblici e misurare lo scarto:

| Livello | Identità | Esito verificato (2023) |
|---|---|---|
| **Provinciale (ISTAT)** | PIL = VA + Imposte nette sui prodotti | scarto max 1 M€ su 107 province |
| **Provinciale (cross-fonte)** | PIL Eurostat NUTS3 vs PIL ISTAT | scarto medio ponderato ~0,09% (max 0,66%), costante entro regione |
| **Nazionale (spesa)** | PIL = Consumi + Investimenti + Export − Import | scarto ~0 (2.142.744 vs 2.142.744 M€) |
| **Nazionale (reddito)** | PIL = Redditi da lavoro + Risultato gestione + Imposte nette | scarto ~0 (2.142.744 vs 2.142.744 M€) |
| **Imprese (SBS)** | VA = Salari + Contributi sociali + Risultato lordo di gestione | scarto max 0,4 M€ (settori market, ~56% del GVA) |

**Cosa dicono i numeri.** Le identità nazionali e quelle ISTAT/SBS chiudono all'esatto
perché sono componenti dello *stesso* dataset: confermano la coerenza interna della fonte,
non un controllo indipendente. Il confronto informativo è Eurostat↔ISTAT: lo scarto è
~0,09% e **costante entro la regione** (es. Liguria +0,66%, Calabria +0,33%, Sicilia +0,17%,
segno variabile tra regioni), quindi è una **correzione di calibrazione regionale**, non
rumore provinciale. A livello nazionale le due fonti coincidono allo 0,005%: le differenze
provinciali sono redistribuzioni dentro lo stesso totale. Nota: Eurostat compila il NUTS3
italiano *da* ISTAT, quindi le due fonti non sono pienamente indipendenti — lo scarto
riflette revisioni/metodologia (vintage NUTS, ESA, aggiustamenti regionali).

Limiti dichiarati: a NUTS3 non esistono le scomposizioni per reddito/spesa (solo GVA
per NACE), quindi il wedge imposte sui prodotti è noto solo a livello nazionale. La
ricomposizione da microdati d'impresa non è fattibile (dati riservati/a pagamento,
economia non osservata): per questo si lavora su componenti pubbliche e riconciliazione.

## Mart

| Mart | Righe | Cosa |
|---|---|---|
| `mart_hub` | 32.500 | EU NUTS3 (107 province IT): PIL, GVA, occupazione, produttività, GFCF, turismo, reati |
| `mart_settori` | 18.900 | GVA per 7 macro-settori NACE × provincia, share % normalizzate |
| `mart_settori_trend` | 18.900 | Variazioni share (pp) e crescita GVA anno su anno per settore |
| `mart_trend_integrato` | 1.300 | CAGR multi-indicatore per provincia (PIL, GVA, occupazione) |
| `mart_domanda` | 2.091 | PIL per componenti della domanda (41 paesi × 1975–2025) |
| `mart_trimestrale` | 776 | PIL trimestrale Italia, 1978–2026 |
| `mart_riconciliazione` | 2.568 | PIL provinciale: Eurostat vs ISTAT vs identità VA+imposte |
| `mart_pil_componenti` | 31 | Identità reddito/spesa del PIL Italia (1995–2025) |
| `mart_imprese_sintesi` | 2.044 | VA imprese (SBS): identità reddito per dimensione e NACE, 2008–2024 |

## Data Dictionary

### mart_riconciliazione (per provincia NUTS3, per anno)

| Colonna | Tipo | Descrizione |
|---|---|---|
| `year` / `geo` / `territorio_nome` | — | Anno, codice ISTAT, nome provincia |
| `geo_nuts2021` | str | Codice NUTS 2021 usato per il join (Eurostat). ISTAT usa NUTS 2013: 54 codici rimappati |
| `eurostat_gdp_mio` | double | PIL Eurostat NUTS3 (MIO_EUR, prezzi correnti) |
| `eurostat_gva_mio` | double | GVA Eurostat NUTS3 (CP_MEUR, NACE TOTAL) |
| `istat_pil_mio` | double | PIL ISTAT (conti territoriali) |
| `istat_va_mio` | double | Valore aggiunto ISTAT |
| `istat_imposte_mio` | double | Imposte nette sui prodotti ISTAT |
| `istat_va_piu_imposte_mio` | double | VA + imposte (ricomposizione) |
| `istat_identita_scarto_mio` | double | PIL − (VA + imposte): atteso ~0 |
| `eurostat_vs_istat_pil_pct` | double | Scarto % PIL Eurostat vs ISTAT |
| `eurostat_vs_istat_va_pct` | double | Scarto % GVA Eurostat vs VA ISTAT |
| `eurostat_pil_su_va` / `istat_pil_su_va` | double | Wedge PIL/GVA per fonte |

### mart_pil_componenti (per anno, Italia)

Componenti in M€ (prezzi correnti) da Eurostat NAMA_10_GDP: `pil`, `consumi_finali`,
`formazione_capitale_lorda`, `gfcf`, `export`, `import`, `redditi_lavoro`,
`risultato_lordo_gestione`, `imposte_nette_produzione_import`, più le colonne derivate
`spesa_totale_mio` / `reddito_totale_mio` e i relativi `*_scarto_mio`, `quota_lavoro_pct`,
`quota_capitale_pct`.

### mart_hub (per provincia NUTS3, per anno)

| Colonna | Unità | Descrizione |
|---|---|---|
| `pil_procapite_eur` | EUR/hab | PIL pro-capite ai prezzi di mercato (Eurostat) |
| `gva_totale_mio` | M EUR | Valore aggiunto lordo totale (prezzi correnti) |
| `occupati_migliaia` | migliaia | Occupati totali (wstatus=EMP, nace=TOTAL) |
| `produttivita_lavoro_eur` | EUR/occ | Produttività del lavoro nominale |
| `gfcf_totale_mio` | M EUR | Formazione di capitale lordo (NUTS2, join su regione) |
| `popolazione` | persone | Derivata: PIL totale / PIL pro-capite |
| `presenze_turistiche_migliaia` | migliaia | Presenze turistiche (I551–I553) |
| `reati_per_100k` | ogni 100k ab. | Reati registrati per 100.000 abitanti |
| `gva_procapite_eur` / `gva_per_lavoratore_eur` | EUR | Derivate |
| `tasso_occupazione_pct` / `gfcf_su_va_pct` | % | Derivate |

**Note:** GFCF è a livello NUTS2 (aggregando il VA delle province della stessa regione).
La popolazione è derivata, non da censimento. I CAGR in `mart_trend_integrato` sono su
valori nominali, non misurano crescita reale.

### mart_settori / mart_settori_trend

GVA per 7 macro-settori NACE (A, B-E, F, G-J, K-N, O-U, R-U) × provincia. Share
normalizzate a 100% per geo/year (i macro-settori Eurostat a NUTS3 non sommano
esattamente al TOTAL). `mart_settori_trend` aggiunge `share_delta_pp` e `gva_yoy_pct`.

## Dashboard

Dashboard Streamlit con 6 pagine:

| Pagina | Contenuto |
|---|---|
| **Panoramica** | KPI (PIL pro-capite, produttività, investimento, occupazione, CAGR) + scarto Eurostat/ISTAT |
| **Territorio** | Mappa choropleth + treemap province, top/bottom, trend temporale |
| **Settori** | GVA per macro-settore, evoluzione, heatmap, variazioni composizione |
| **Domanda** | Composizione PIL, waterfall saldo commerciale, trimestrale |
| **Riconciliazione** | Identità reddito/spesa nazionale, scarti Eurostat vs ISTAT per provincia, identità VA imprese (SBS) |
| **Convergenza** | Box plot macro-area, CAGR, scatter convergenza, gap Nord-Sud |

```bash
cd dashboard && streamlit run app.py
```

## Come funziona

```
Eurostat SDMX + ISTAT conti territoriali → toolkit (mart) → parquet → GCS → dashboard
```

Il dataset è **mart-only compose**: non ha raw né clean propri. Gli SQL leggono
direttamente dai parquet clean/mart degli upstream su GCS (`support: type: external`).

```bash
# Compose (legge da GCS HTTPS)
make compose

# Registry (artifact catalogo)
make registry-write

# Dashboard
make dashboard
```

**CI** — la workflow `.github/workflows/pipeline.yml` usa la pipeline riutilizzabile
org: esegue `make compose`, sincronizza i mart su `gs://dataciviclab-mart/pil-intelligence/`
e apre una PR draft col registry aggiornato. I parquet **non** sono committati nel repo.

## Fonti

| Fonte | Cosa fornisce |
|---|---|
| Eurostat — `NAMA_10R_3GDP` | PIL pro-capite e totale NUTS3 |
| Eurostat — `NAMA_10R_3GVA` | GVA per settore NACE × NUTS3 |
| Eurostat — `NAMA_10R_3EMPERS` | Occupati per settore × NUTS3 |
| Eurostat — `NAMA_10R_3NLP` | Produttività del lavoro NUTS3 |
| Eurostat — `NAMA_10R_2GFCF` | Formazione di capitale lordo NUTS2 |
| Eurostat — `NAMA_10_GDP` | Componenti reddito/spesa del PIL (nazionale) |
| Eurostat — `NAMQ_10_GDP` | PIL trimestrale Italia |
| ISTAT — conti territoriali (DCCN_PILT) | PIL, VA, imposte nette per provincia |
| ISTAT — SBS (statistiche strutturali) | VA, salari, contributi, margini per dimensione d'impresa |
| Eurostat — `TOUR_OCC_NIN2`, `CRIM_GEN_REG` | Turismo, reati NUTS3 |
| GISCO / Eurostat | Confini NUTS3 per la mappa (choropleth) |

## Perché fidarsi

- Fonti ufficiali Eurostat e ISTAT
- Trasformazioni documentate in SQL; parquet pubblicati su GCS e nel registry
- Riconciliazione multi-fonte con scarti misurati, non nascosti
- Data dictionary esplicito con note metodologiche e limiti

## Licenza

- **Dati**: CC BY 4.0
- **Codice**: MIT
