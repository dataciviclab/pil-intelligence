-- mart_riconciliazione.sql — PIL provinciale: Eurostat vs ISTAT vs identità contabile
--
-- Grana: (year, geo). Solo Italia, 2000-2023.
-- Tre letture indipendenti dello stesso PIL provinciale:
--   1. Eurostat NUTS3 (NAMA_10R_3GDP, MIO_EUR) — codici NUTS 2021 (ITH/ITI, ITC4C...)
--   2. ISTAT conti territoriali (PIL dichiarato) — codici NUTS 2013 (ITD/ITE, ITC45...)
--   3. identità produzione ISTAT: PIL = VA + Imposte nette sui prodotti
--
-- ATTENZIONE vintage: le due fonti usano NUTS diversi (2021 vs 2013), quindi il
-- join per codice NON è diretto. nuts_map rimappa i codici ISTAT sui NUTS 2021
-- (54 codici; i restanti 53 coincidono). Mappatura derivata per nome (GISCO
-- NUTS 2021). Senza la mappa, solo 53/107 province si riconcilierebbero.

WITH nuts_map AS (
    SELECT istat_code, nuts2021 FROM (VALUES
        ('IT108','ITC4D'),('IT109','ITI35'),('IT110','ITF48'),('IT111','ITG2H'),
        ('ITC45','ITC4C'),
        ('ITD10','ITH10'),('ITD20','ITH20'),
        ('ITD31','ITH31'),('ITD32','ITH32'),('ITD33','ITH33'),('ITD34','ITH34'),
        ('ITD35','ITH35'),('ITD36','ITH36'),('ITD37','ITH37'),
        ('ITD41','ITH41'),('ITD42','ITH42'),('ITD43','ITH43'),('ITD44','ITH44'),
        ('ITD51','ITH51'),('ITD52','ITH52'),('ITD53','ITH53'),('ITD54','ITH54'),
        ('ITD55','ITH55'),('ITD56','ITH56'),('ITD57','ITH57'),('ITD58','ITH58'),
        ('ITD59','ITH59'),
        ('ITE11','ITI11'),('ITE12','ITI12'),('ITE13','ITI13'),('ITE14','ITI14'),
        ('ITE15','ITI15'),('ITE16','ITI16'),('ITE17','ITI17'),('ITE18','ITI18'),
        ('ITE19','ITI19'),('ITE1A','ITI1A'),('ITE21','ITI21'),('ITE22','ITI22'),
        ('ITE31','ITI31'),('ITE32','ITI32'),('ITE33','ITI33'),('ITE34','ITI34'),
        ('ITE41','ITI41'),('ITE42','ITI42'),('ITE43','ITI43'),('ITE44','ITI44'),
        ('ITE45','ITI45'),
        ('ITF41','ITF46'),('ITF42','ITF47'),
        ('ITG25','ITG2D'),('ITG26','ITG2E'),('ITG27','ITG2F'),('ITG28','ITG2G')
    ) AS t(istat_code, nuts2021)
),
eu_gdp AS (
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
    COALESCE(m.nuts2021, i.geo) AS geo_nuts2021,
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
    -- (nessuna colonna per GVA: Eurostat GVA NUTS3 == ISTAT VA esatto, scarto 0 su tutte
    --  le righe — Eurostat non ri-stima il valore aggiunto, lo copia da ISTAT)
    ROUND((eu.eurostat_gdp_mio / i.istat_pil_mio - 1) * 100, 2) AS eurostat_vs_istat_pil_pct,
    -- wedge PIL/GVA (imposte nette sui prodotti come quota)
    ROUND(eu.eurostat_gdp_mio / ev.eurostat_gva_mio, 4) AS eurostat_pil_su_va,
    ROUND(i.istat_pil_mio / i.istat_va_mio, 4) AS istat_pil_su_va
FROM istat i
LEFT JOIN nuts_map m ON i.geo = m.istat_code
LEFT JOIN eu_gdp eu ON i.year = eu.year AND COALESCE(m.nuts2021, i.geo) = eu.geo
LEFT JOIN eu_gva ev ON i.year = ev.year AND COALESCE(m.nuts2021, i.geo) = ev.geo
ORDER BY i.year, i.geo
