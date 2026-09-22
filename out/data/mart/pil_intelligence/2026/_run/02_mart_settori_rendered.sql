-- mart_settori.sql — PIL Intelligence: GVA per settore NACE x NUTS3 x year
--
-- Grana: (year, geo, nace_r2).
-- Calcola il valore GVA e la share percentuale su totale per ogni settore.
-- Solo NUTS3 italiane (country = 'IT').
-- Le share sono normalizzate per sommare esattamente a 100% per ogni geo/year,
-- perché i7 macro-settori Eurostat a NUTS3 non sommano esattamente al TOTAL.

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
),
base AS (
    SELECT
        g.year, g.geo, g.geo_label_en, g.country,
        g.nace_r2, g.nace_r2_label_en,
        g.gva_valore_mio,
        t.gva_totale_mio,
        CASE WHEN t.gva_totale_mio > 0
             THEN g.gva_valore_mio / t.gva_totale_mio * 100
             END AS share_raw
    FROM gva g
    LEFT JOIN gva_totale t ON g.year = t.year AND g.geo = t.geo
    WHERE g.country = 'IT'
),
share_sum AS (
    SELECT year, geo, SUM(share_raw) AS total_raw
    FROM base
    WHERE share_raw IS NOT NULL
    GROUP BY year, geo
)
SELECT
    b.year, b.geo, b.geo_label_en, b.country,
    b.nace_r2, b.nace_r2_label_en,
    b.gva_valore_mio,
    b.gva_totale_mio,
    CASE WHEN s.total_raw > 0
         THEN ROUND(b.share_raw / s.total_raw * 100, 2)
         END AS share_pct
FROM base b
LEFT JOIN share_sum s ON b.year = s.year AND b.geo = s.geo
ORDER BY b.year, b.geo, b.gva_valore_mio DESC
