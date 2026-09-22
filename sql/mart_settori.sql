-- mart_settori.sql — PIL Intelligence: GVA per settore NACE x NUTS3 x year
--
-- Grana: (year, geo, nace_r2).
-- Calcola il valore GVA e la share percentuale su totale per ogni settore.
-- Solo NUTS3 italiane (country = 'IT').

WITH gva AS (
    SELECT year, geo, geo_label_en, nuts_level, country,
           nace_r2, nace_r2_label_en, value AS gva_valore_mio
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gva_nuts3/eurostat_gva_nuts3_2026_clean.parquet')
    WHERE unit = 'CP_MEUR' AND nuts_level = 'NUTS3'
      AND nace_r2 IN ('A', 'B-E', 'F', 'G-J', 'K-N', 'O-U', 'R-U')
),
gva_totale AS (
    SELECT year, geo, value AS gva_totale_mio
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gva_nuts3/eurostat_gva_nuts3_2026_clean.parquet')
    WHERE unit = 'CP_MEUR' AND nace_r2 = 'TOTAL' AND nuts_level = 'NUTS3'
)
SELECT
    g.year,
    g.geo,
    g.geo_label_en,
    g.country,
    g.nace_r2,
    g.nace_r2_label_en,
    g.gva_valore_mio,
    t.gva_totale_mio,
    CASE WHEN t.gva_totale_mio > 0
         THEN ROUND(g.gva_valore_mio / t.gva_totale_mio * 100, 2)
         END AS share_pct
FROM gva g
LEFT JOIN gva_totale t ON g.year = t.year AND g.geo = t.geo
WHERE g.country = 'IT'
ORDER BY g.year, g.geo, g.gva_valore_mio DESC
