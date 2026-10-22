-- mart_pil_componenti.sql — identità reddito e spesa del PIL (Italia, nazionale)
--
-- Grana: (year). Fonte Eurostat NAMA_10_GDP (CP_MEUR, prezzi correnti).
-- Ricompone il PIL dai componenti indipendenti e ne misura lo scarto:
--   spesa:   PIL = P3 + P5G + P6 - P7          (consumi + investimenti + export - import)
--   reddito: PIL = D1 + B2A3G + D2X3          (lavoro + risultato gestione + imposte nette)
-- Uno scarto ~0 conferma che i componenti chiudono sul PIL dichiarato.

WITH base AS (
    SELECT year, na_item, value
    FROM read_parquet('{support.eurostat_nama10_gdp_clean.path}')
    WHERE unit = 'CP_MEUR' AND country = 'IT'
),
pivoted AS (
    SELECT
        year,
        MAX(CASE WHEN na_item = 'B1GQ' THEN value END) AS pil,
        MAX(CASE WHEN na_item = 'P3' THEN value END) AS consumi_finali,
        MAX(CASE WHEN na_item = 'P5G' THEN value END) AS formazione_capitale_lorda,
        MAX(CASE WHEN na_item = 'P51G' THEN value END) AS gfcf,
        MAX(CASE WHEN na_item = 'P6' THEN value END) AS export,
        MAX(CASE WHEN na_item = 'P7' THEN value END) AS import,
        MAX(CASE WHEN na_item = 'D1' THEN value END) AS redditi_lavoro,
        MAX(CASE WHEN na_item = 'B2A3G' THEN value END) AS risultato_lordo_gestione,
        MAX(CASE WHEN na_item = 'D2X3' THEN value END) AS imposte_nette_produzione_import
    FROM base
    GROUP BY year
)
SELECT
    year,
    pil,
    consumi_finali,
    formazione_capitale_lorda,
    gfcf,
    export,
    import,
    redditi_lavoro,
    risultato_lordo_gestione,
    imposte_nette_produzione_import,
    -- identità spesa
    ROUND(consumi_finali + formazione_capitale_lorda + export - import, 1) AS spesa_totale_mio,
    ROUND(pil - (consumi_finali + formazione_capitale_lorda + export - import), 1) AS spesa_scarto_mio,
    ROUND((consumi_finali + formazione_capitale_lorda + export - import) / pil * 100, 2) AS spesa_su_pil_pct,
    -- identità reddito
    ROUND(redditi_lavoro + risultato_lordo_gestione + imposte_nette_produzione_import, 1) AS reddito_totale_mio,
    ROUND(pil - (redditi_lavoro + risultato_lordo_gestione + imposte_nette_produzione_import), 1) AS reddito_scarto_mio,
    ROUND((redditi_lavoro + risultato_lordo_gestione + imposte_nette_produzione_import) / pil * 100, 2) AS reddito_su_pil_pct,
    -- quote sul PIL
    ROUND(redditi_lavoro / pil * 100, 1) AS quota_lavoro_pct,
    ROUND(risultato_lordo_gestione / pil * 100, 1) AS quota_capitale_pct
FROM pivoted
WHERE pil IS NOT NULL
ORDER BY year
