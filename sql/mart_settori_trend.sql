-- mart_settori_trend.sql — PIL Intelligence: trend composizione settoriale
--
-- Grana: (year, geo, nace_r2) — stessa di mart_settori.
-- Aggiunge variazione annua share e variazione GVA con LAG window.
-- Solo NUTS3 italiane (country = 'IT').
-- Le share sono normalizzate per sommare a 100% (vedi mart_settori.sql).

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
base_raw AS (
    SELECT
        g.year, g.geo, g.geo_label_en, g.country,
        g.nace_r2, g.nace_r2_label_en,
        g.gva_valore_mio, t.gva_totale_mio,
        CASE WHEN t.gva_totale_mio > 0
             THEN g.gva_valore_mio / t.gva_totale_mio * 100
             END AS share_raw
    FROM gva g
    LEFT JOIN gva_totale t ON g.year = t.year AND g.geo = t.geo
    WHERE g.country = 'IT'
),
share_sum AS (
    SELECT year, geo, SUM(share_raw) AS total_raw
    FROM base_raw WHERE share_raw IS NOT NULL
    GROUP BY year, geo
),
base AS (
    SELECT
        b.year, b.geo, b.geo_label_en, b.country,
        b.nace_r2, b.nace_r2_label_en,
        b.gva_valore_mio, b.gva_totale_mio,
        CASE WHEN s.total_raw > 0
             THEN ROUND(b.share_raw / s.total_raw * 100, 2)
             END AS share_pct
    FROM base_raw b
    LEFT JOIN share_sum s ON b.year = s.year AND b.geo = s.geo
)
SELECT
    year, geo, geo_label_en, country,
    nace_r2, nace_r2_label_en,
    gva_valore_mio, gva_totale_mio, share_pct,

    LAG(share_pct) OVER (PARTITION BY geo, nace_r2 ORDER BY year) AS share_pct_prev,
    CASE WHEN LAG(share_pct) OVER (PARTITION BY geo, nace_r2 ORDER BY year) IS NOT NULL AND share_pct IS NOT NULL
         THEN ROUND(share_pct - LAG(share_pct) OVER (PARTITION BY geo, nace_r2 ORDER BY year), 2)
         END AS share_delta_pp,

    LAG(gva_valore_mio) OVER (PARTITION BY geo, nace_r2 ORDER BY year) AS gva_prev,
    CASE WHEN LAG(gva_valore_mio) OVER (PARTITION BY geo, nace_r2 ORDER BY year) IS NOT NULL
              AND gva_valore_mio IS NOT NULL
              AND LAG(gva_valore_mio) OVER (PARTITION BY geo, nace_r2 ORDER BY year) > 0
         THEN ROUND((gva_valore_mio / LAG(gva_valore_mio) OVER (PARTITION BY geo, nace_r2 ORDER BY year) - 1) * 100, 2)
         END AS gva_yoy_pct

FROM base
ORDER BY year, geo, gva_valore_mio DESC
