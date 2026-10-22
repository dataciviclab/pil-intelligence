-- mart_convergenza.sql — le province convergono o divergono? (2000-2023)
--
-- Grana: (year). Misure di dispersione del PIL pro-capite tra le province italiane.
-- sigma_log = deviazione standard del log(PIL pro-capite): SCENDE = convergenza,
-- SALE = divergenza. gap_nord_sud = media Nord-Ovest/Nord-Est / media Sud/Isole.
-- ATTENZIONE: PIL a prezzi correnti (nominale) — non è convergenza reale.

WITH base AS (
    SELECT year, geo, value AS pil_procapite_eur
    FROM read_parquet('{support.eurostat_gdp_nuts3.path}')
    WHERE unit = 'EUR_HAB' AND nuts_level = 'NUTS3' AND country = 'IT' AND value IS NOT NULL
)
SELECT
    year,
    count(*) AS n_province,
    round(avg(pil_procapite_eur)) AS media_eur,
    round(median(pil_procapite_eur)) AS mediana_eur,
    -- sigma-convergenza: dispersione in scala log
    round(stddev_samp(ln(pil_procapite_eur)), 4) AS sigma_log,
    round(stddev_samp(pil_procapite_eur) / avg(pil_procapite_eur) * 100, 1) AS cv_pct,
    round(
        quantile_cont(pil_procapite_eur, 0.9) / quantile_cont(pil_procapite_eur, 0.1), 2
    ) AS p90_su_p10,
    -- gap Nord (ITC+ITH) vs Sud (ITF+ITG)
    round(avg(pil_procapite_eur) FILTER (WHERE geo LIKE 'ITC%' OR geo LIKE 'ITH%')) AS nord_eur,
    round(avg(pil_procapite_eur) FILTER (WHERE geo LIKE 'ITF%' OR geo LIKE 'ITG%')) AS sud_eur,
    round(
        avg(pil_procapite_eur) FILTER (WHERE geo LIKE 'ITC%' OR geo LIKE 'ITH%')
        / avg(pil_procapite_eur) FILTER (WHERE geo LIKE 'ITF%' OR geo LIKE 'ITG%'), 2
    ) AS gap_nord_sud
FROM base
GROUP BY year
ORDER BY year
