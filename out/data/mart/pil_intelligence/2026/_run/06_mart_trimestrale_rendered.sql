-- mart_trimestrale.sql — PIL Intelligence: PIL trimestrale Italia
--
-- Da NAMQ_10_GDP (support qgdp), unità CLV_PCH_PRE (% variazione trimestrale).
-- Grana: (year, quarter, na_item).

SELECT
    year, quarter, na_item, na_item_label_en, value
FROM read_parquet('https://storage.googleapis.com/dataciviclab-mart/eurostat/eurostat_namq10_gdp/mart_quarterly.parquet')
WHERE country = 'IT'
  AND unit = 'CLV_PCH_PRE'
  AND na_item IN ('B1GQ', 'P3', 'P6', 'P7')
ORDER BY year, quarter, na_item
