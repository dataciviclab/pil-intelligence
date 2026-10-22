-- mart_imprese_sintesi.sql — valore aggiunto delle imprese: identità reddito
--
-- Grana: (anno, nace_codice, size_class) — nazionale (ISTAT SBS).
-- Verifica l'identità reddito del valore aggiunto:
--   VA (al costo fattore) = Salari e stipendi + Contributi sociali + Risultato lordo di gestione
-- Scope: solo settori market (SBS), NON è il PIL: copre ~56% del GVA totale.
-- I valori clean sono in migliaia di euro → convertiti in M€ (/1000).

WITH base AS (
    SELECT anno, size_class, nace_codice, nace, indicatore, valore
    FROM read_parquet('{support.istat_sbs_imprese.path}')
    WHERE grain = 'nazionale'
),
pivoted AS (
    SELECT
        anno,
        size_class,
        nace_codice,
        MAX(nace) AS nace,
        MAX(CASE WHEN indicatore = 'Valore aggiunto al costo fattore' THEN valore END) AS va_mila,
        MAX(CASE WHEN indicatore = 'Salari e stipendi' THEN valore END) AS salari_mila,
        MAX(CASE WHEN indicatore = 'Contributi sociali' THEN valore END) AS contributi_mila,
        MAX(CASE WHEN indicatore = 'Risultato lordo di gestione' THEN valore END) AS gos_mila,
        MAX(CASE WHEN indicatore = 'Valore della produzione' THEN valore END) AS produzione_mila,
        MAX(CASE WHEN indicatore = 'Imprese' THEN valore END) AS imprese
    FROM base
    GROUP BY anno, size_class, nace_codice
)
SELECT
    anno,
    nace_codice,
    nace,
    size_class,
    ROUND(va_mila / 1000, 1) AS va_mio,
    ROUND(salari_mila / 1000, 1) AS salari_mio,
    ROUND(contributi_mila / 1000, 1) AS contributi_mio,
    ROUND(gos_mila / 1000, 1) AS gos_mio,
    ROUND(produzione_mila / 1000, 1) AS produzione_mio,
    imprese,
    -- identità reddito: ricomposizione del VA dai componenti
    ROUND((salari_mila + contributi_mila + gos_mila) / 1000, 1) AS va_ricomposto_mio,
    ROUND((va_mila - (salari_mila + contributi_mila + gos_mila)) / 1000, 1) AS identita_scarto_mio,
    ROUND((salari_mila + contributi_mila) / NULLIF(va_mila, 0) * 100, 1) AS quota_lavoro_pct,
    ROUND(gos_mila / NULLIF(va_mila, 0) * 100, 1) AS quota_capitale_pct
FROM pivoted
WHERE va_mila IS NOT NULL
ORDER BY anno, nace_codice, size_class
