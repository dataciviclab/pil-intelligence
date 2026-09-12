-- mart_trend_integrato.sql — PIL Intelligence: CAGR e growth multi-indicatore
--
-- Grana: (geo) — una riga per NUTS3 regione.
-- Prima/ultima anno disponibile per PIL, GVA, occupazione + CAGR.

WITH pil AS (
    SELECT year, geo, value AS pil
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gdp_nuts3/eurostat_gdp_nuts3_2026_clean.parquet')
    WHERE unit = 'EUR_HAB' AND nuts_level = 'NUTS3'
),
pil_bounds AS (
    SELECT geo,
           MIN(year) FILTER (WHERE pil IS NOT NULL) AS first_year,
           MAX(year) FILTER (WHERE pil IS NOT NULL) AS last_year,
           COUNT(*) FILTER (WHERE pil IS NOT NULL) AS years_observed
    FROM pil GROUP BY geo
),
pil_first AS (
    SELECT p.geo, p.pil AS first_value
    FROM pil p JOIN pil_bounds b ON p.geo = b.geo AND p.year = b.first_year
),
pil_last AS (
    SELECT p.geo, p.pil AS last_value
    FROM pil p JOIN pil_bounds b ON p.geo = b.geo AND p.year = b.last_year
),

gva AS (
    SELECT year, geo, value AS gva
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gva_nuts3/eurostat_gva_nuts3_2026_clean.parquet')
    WHERE unit = 'CP_MEUR' AND nace_r2 = 'TOTAL' AND nuts_level = 'NUTS3'
),
gva_bounds AS (
    SELECT geo, MIN(year) FILTER (WHERE gva IS NOT NULL) AS first_year, MAX(year) FILTER (WHERE gva IS NOT NULL) AS last_year
    FROM gva GROUP BY geo
),
gva_first AS (
    SELECT g.geo, g.gva AS first_value
    FROM gva g JOIN gva_bounds b ON g.geo = b.geo AND g.year = b.first_year
),
gva_last AS (
    SELECT g.geo, g.gva AS last_value
    FROM gva g JOIN gva_bounds b ON g.geo = b.geo AND g.year = b.last_year
),

emp AS (
    SELECT year, geo, value AS emp
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_emp_nuts3/eurostat_emp_nuts3_2026_clean.parquet')
    WHERE unit = 'THS' AND wstatus = 'EMP' AND nace_r2 = 'TOTAL' AND nuts_level = 'NUTS3'
),
emp_bounds AS (
    SELECT geo, MIN(year) FILTER (WHERE emp IS NOT NULL) AS first_year, MAX(year) FILTER (WHERE emp IS NOT NULL) AS last_year
    FROM emp GROUP BY geo
),
emp_first AS (
    SELECT e.geo, e.emp AS first_value
    FROM emp e JOIN emp_bounds b ON e.geo = b.geo AND e.year = b.first_year
),
emp_last AS (
    SELECT e.geo, e.emp AS last_value
    FROM emp e JOIN emp_bounds b ON e.geo = b.geo AND e.year = b.last_year
)

SELECT
    b.geo,
    g.geo_label_en,
    g.nuts_level,
    g.country,
    b.first_year AS pil_first_year,
    b.last_year AS pil_last_year,
    b.years_observed,

    pf.first_value AS pil_first,
    pl.last_value AS pil_last,
    pl.last_value - pf.first_value AS pil_delta_abs,
    ROUND((pl.last_value / NULLIF(pf.first_value, 0) - 1) * 100, 2) AS pil_delta_pct,
    ROUND(
        (POWER(pl.last_value / NULLIF(pf.first_value, 0), 1.0 / NULLIF(b.years_observed - 1, 0)) - 1) * 100,
        3
    ) AS pil_cagr_pct,

    gf.first_value AS gva_first,
    gl.last_value AS gva_last,
    ROUND((gl.last_value / NULLIF(gf.first_value, 0) - 1) * 100, 2) AS gva_delta_pct,

    ef.first_value AS emp_first,
    el.last_value AS emp_last,
    ROUND((el.last_value / NULLIF(ef.first_value, 0) - 1) * 100, 2) AS emp_delta_pct

FROM pil_bounds b
JOIN (SELECT DISTINCT geo, geo_label_en, nuts_level, country FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/eurostat/eurostat_gdp_nuts3/eurostat_gdp_nuts3_2026_clean.parquet') WHERE nuts_level = 'NUTS3') g ON b.geo = g.geo
LEFT JOIN pil_first pf ON b.geo = pf.geo
LEFT JOIN pil_last pl  ON b.geo = pl.geo
LEFT JOIN gva_first gf ON b.geo = gf.geo
LEFT JOIN gva_last gl  ON b.geo = gl.geo
LEFT JOIN emp_first ef ON b.geo = ef.geo
LEFT JOIN emp_last el  ON b.geo = el.geo
ORDER BY pil_cagr_pct DESC NULLS LAST
