-- mart_domanda.sql — PIL Intelligence: composizione della domanda (Italia)
--
-- Crocicchio PIL aggregato × componenti della domanda.
-- Da NAMA_10_GDP (support exp), unità CP_MEUR.

SELECT
    year,
    country,
    pil,
    consumi_finali,
    gfcf,
    formazione_capitale,
    export,
    import,
    domanda_interna,
    errore_omissione,

    CASE WHEN pil > 0 THEN ROUND(consumi_finali / pil * 100, 1) END AS consumi_pct_pil,
    CASE WHEN pil > 0 AND gfcf IS NOT NULL THEN ROUND(gfcf / pil * 100, 1) END AS gfcf_pct_pil,
    CASE WHEN pil > 0 THEN ROUND(export / pil * 100, 1) END AS export_pct_pil,
    CASE WHEN pil > 0 THEN ROUND(import / pil * 100, 1) END AS import_pct_pil,
    CASE WHEN pil > 0 THEN ROUND((export - import) / pil * 100, 1) END AS saldo_commerciale_pct_pil

FROM read_parquet('https://storage.googleapis.com/dataciviclab-mart/eurostat/eurostat_nama10_gdp/mart_expenditure.parquet')
WHERE unit = 'CP_MEUR'
ORDER BY year, country
