-- mart_riconciliazione.sql — PIL provinciale: Eurostat vs ISTAT vs identità contabile
--
-- Grana: (year, geo NUTS3). Solo Italia, 2000-2023.
-- Tre letture indipendenti dello stesso PIL provinciale:
--   1. Eurostat NUTS3 (NAMA_10R_3GDP, MIO_EUR)
--   2. ISTAT conti territoriali (PIL dichiarato, prezzi correnti)
--   3. identità produzione ISTAT: PIL = VA + Imposte nette sui prodotti
-- Le colonne di scarto misurano quanto le fonti divergono.
--
-- Join su codice NUTS3: ISTAT usa gli stessi codici (es. ITC11 = Torino).

WITH eu_gdp AS (
    SELECT year, geo, value AS eurostat_gdp_mio
    FROM read_parquet('{support.eurostat_gdp_nuts3.path}')
    WHERE unit = 'MIO_EUR' AND nuts_level = 'NUTS3' AND country = 'IT'
),
eu_gva AS (
    SELECT year, geo, value AS eurostat_gva_mio
    FROM read_parquet('{support.eurostat_gva_nuts3.path}')
    WHERE unit = 'CP_MEUR' AND nace_r2 = 'TOTAL' AND nuts_level = 'NUTS3' AND country = 'IT'
),
istat AS (
    SELECT
        anno AS year,
        territorio_codice AS geo,
        MAX(territorio_nome) AS territorio_nome,
        MAX(CASE WHEN tipo_dato = 'PIL' THEN valore_mln_eu END) AS istat_pil_mio,
        MAX(CASE WHEN tipo_dato = 'VA' THEN valore_mln_eu END) AS istat_va_mio,
        MAX(CASE WHEN tipo_dato = 'Imposte nette prodotti' THEN valore_mln_eu END) AS istat_imposte_mio
    FROM read_parquet('{support.istat_pil_territoriale.path}')
    WHERE livello = 'provincia'
    GROUP BY anno, territorio_codice
)
SELECT
    i.year,
    i.geo,
    i.territorio_nome,
    eu.eurostat_gdp_mio,
    ev.eurostat_gva_mio,
    i.istat_pil_mio,
    i.istat_va_mio,
    i.istat_imposte_mio,
    ROUND(i.istat_va_mio + i.istat_imposte_mio, 1) AS istat_va_piu_imposte_mio,
    -- identità ISTAT: dovrebbe essere ~0 (VA + imposte = PIL)
    ROUND(i.istat_pil_mio - (i.istat_va_mio + i.istat_imposte_mio), 1) AS istat_identita_scarto_mio,
    -- cross-source: Eurostat vs ISTAT
    ROUND((eu.eurostat_gdp_mio / i.istat_pil_mio - 1) * 100, 2) AS eurostat_vs_istat_pil_pct,
    ROUND((ev.eurostat_gva_mio / i.istat_va_mio - 1) * 100, 2) AS eurostat_vs_istat_va_pct,
    -- wedge PIL/GVA (imposte nette sui prodotti come quota)
    ROUND(eu.eurostat_gdp_mio / ev.eurostat_gva_mio, 4) AS eurostat_pil_su_va,
    ROUND(i.istat_pil_mio / i.istat_va_mio, 4) AS istat_pil_su_va
FROM istat i
LEFT JOIN eu_gdp eu ON i.year = eu.year AND i.geo = eu.geo
LEFT JOIN eu_gva ev ON i.year = ev.year AND i.geo = ev.geo
ORDER BY i.year, i.geo
