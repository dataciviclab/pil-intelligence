-- mart_debito_fisco.sql — PIL Intelligence: debito x fisco Italia (serie lunga)
--
-- Crocicchio PIL + debito + saldo primario + interessi.
-- Grana: (anno). Solo Italia, 1861-2025.
-- debito_pil_pct: OCPI serie D (1861-2025) con fallback Eurostat (1995-2025).

WITH pil AS (
    SELECT cast(anno AS integer) AS anno, valore AS pil_nominale_mln
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'B'
),
ocpi_debito AS (
    SELECT cast(anno AS integer) AS anno, valore AS ocpi_debito_pil
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'D'
),
eurostat_debito AS (
    SELECT anno, debito_pil_pct, stock_mln_eur
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/eurostat_debito_pil/2026/eurostat_debito_pil_2026_clean.parquet')
    WHERE settore = 'S13'
),
saldo_primario AS (
    SELECT cast(anno AS integer) AS anno, valore AS saldo_primario_pct
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'G'
),
interessi AS (
    SELECT cast(anno AS integer) AS anno, valore AS interessi_pct_pil
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'I'
),
spread_ig AS (
    SELECT cast(anno AS integer) AS anno, valore AS spread_i_g
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'S'
),
crescita_pil AS (
    SELECT cast(anno AS integer) AS anno, valore AS crescita_pil_reale_pct
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'N'
),
inflazione AS (
    SELECT cast(anno AS integer) AS anno, valore AS inflazione_pct
    FROM read_parquet('https://storage.googleapis.com/dataciviclab-clean/debito_pubblico_intelligence/ocpi_serie_storiche/2026/ocpi_serie_storiche_2026_clean.parquet')
    WHERE serie = 'P'
)
SELECT
    p.anno,
    p.pil_nominale_mln,
    COALESCE(ed.debito_pil_pct, od.ocpi_debito_pil) AS debito_pil_pct,
    ed.stock_mln_eur,
    sp.saldo_primario_pct,
    i.interessi_pct_pil,
    ig.spread_i_g,
    cp.crescita_pil_reale_pct,
    inf.inflazione_pct
FROM pil p
LEFT JOIN ocpi_debito od      ON p.anno = od.anno
LEFT JOIN eurostat_debito ed  ON p.anno = ed.anno
LEFT JOIN saldo_primario sp   ON p.anno = sp.anno
LEFT JOIN interessi i         ON p.anno = i.anno
LEFT JOIN spread_ig ig        ON p.anno = ig.anno
LEFT JOIN crescita_pil cp     ON p.anno = cp.anno
LEFT JOIN inflazione inf      ON p.anno = inf.anno
ORDER BY p.anno
