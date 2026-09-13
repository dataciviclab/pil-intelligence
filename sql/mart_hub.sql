-- mart_hub.sql — PIL Intelligence: indicatori cross per NUTS3 x year
--
-- Una riga per (year, geo) a livello NUTS3.
-- LEFT JOIN dal PIL come base, con indicatori cross-tematici.
-- Popolazione derivata da GDP (MIO_EUR / EUR_HAB).
-- GFCF è a livello NUTS2, joinato su nuts_parent_code.

WITH pil AS (
    SELECT year, geo, geo_label_en, nuts_level, country, nuts_parent_code, nuts_parent_label_en,
           value AS pil_procapite_eur
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gdp_nuts3/eurostat_gdp_nuts3_2026_clean.parquet')
    WHERE unit = 'EUR_HAB' AND nuts_level = 'NUTS3'
),
gdp_tot AS (
    SELECT year, geo, value AS pil_totale_mio
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gdp_nuts3/eurostat_gdp_nuts3_2026_clean.parquet')
    WHERE unit = 'MIO_EUR' AND nuts_level = 'NUTS3'
),
gva_tot AS (
    SELECT year, geo, value AS gva_totale_mio
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gva_nuts3/eurostat_gva_nuts3_2026_clean.parquet')
    WHERE unit = 'CP_MEUR' AND nace_r2 = 'TOTAL' AND nuts_level = 'NUTS3'
),
emp_tot AS (
    SELECT year, geo, value AS occupati_migliaia
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_emp_nuts3/eurostat_emp_nuts3_2026_clean.parquet')
    WHERE unit = 'THS' AND wstatus = 'EMP' AND nace_r2 = 'TOTAL' AND nuts_level = 'NUTS3'
),
prod AS (
    SELECT year, geo, value AS produttivita_lavoro_eur
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_labour_productivity_nuts3/eurostat_labour_productivity_nuts3_2026_clean.parquet')
    WHERE unit = 'EUR' AND nuts_level = 'NUTS3'
),
turismo AS (
    SELECT year, geo, value AS presenze_turistiche_migliaia
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_tourism_nuts3/eurostat_tourism_nuts3_2026_clean.parquet')
    WHERE unit = 'NR' AND c_resid = 'TOTAL' AND nace_r2 = 'I551-I553' AND nuts_level = 'NUTS3'
),
criminalita AS (
    SELECT year, geo, SUM(value) AS reati_per_100k
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_crime_nuts3/eurostat_crime_nuts3_2026_clean.parquet')
    WHERE unit = 'P_HTHAB' AND nuts_level = 'NUTS3'
    GROUP BY year, geo
),
gfcf AS (
    SELECT year, geo AS geo_nuts2, value AS gfcf_totale_mio
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gfcf_nuts2/eurostat_gfcf_nuts2_2026_clean.parquet')
    WHERE sector = 'S1' AND currency = 'MIO_EUR' AND nace_r2 = 'TOTAL'
      AND nuts_level = 'NUTS2'
)
SELECT
    p.year,
    p.geo,
    p.geo_label_en,
    p.nuts_level,
    p.country,
    p.nuts_parent_code,
    p.nuts_parent_label_en,

    CASE WHEN gdp.pil_totale_mio > 0 AND p.pil_procapite_eur > 0
         THEN ROUND(gdp.pil_totale_mio * 1e6 / p.pil_procapite_eur, 0)
         END AS popolazione,
    p.pil_procapite_eur,
    g.gva_totale_mio,
    e.occupati_migliaia,
    pr.produttivita_lavoro_eur,
    t.presenze_turistiche_migliaia,
    c.reati_per_100k,
    gf.gfcf_totale_mio,

    CASE WHEN g.gva_totale_mio IS NOT NULL AND gdp.pil_totale_mio > 0 AND p.pil_procapite_eur > 0
         THEN ROUND(g.gva_totale_mio * 1e6 / (gdp.pil_totale_mio * 1e6 / p.pil_procapite_eur), 0)
         END AS gva_procapite_eur,
    CASE WHEN g.gva_totale_mio IS NOT NULL AND e.occupati_migliaia > 0
         THEN ROUND(g.gva_totale_mio * 1e3 / e.occupati_migliaia, 0)
         END AS gva_per_lavoratore_eur

FROM pil p
LEFT JOIN gdp_tot gdp ON p.year = gdp.year AND p.geo = gdp.geo
LEFT JOIN gva_tot g   ON p.year = g.year AND p.geo = g.geo
LEFT JOIN emp_tot e   ON p.year = e.year AND p.geo = e.geo
LEFT JOIN prod pr     ON p.year = pr.year AND p.geo = pr.geo
LEFT JOIN turismo t   ON p.year = t.year AND p.geo = t.geo
LEFT JOIN criminalita c ON p.year = c.year AND p.geo = c.geo
LEFT JOIN gfcf gf     ON p.year = gf.year AND p.nuts_parent_code = gf.geo_nuts2
ORDER BY p.year, p.geo
