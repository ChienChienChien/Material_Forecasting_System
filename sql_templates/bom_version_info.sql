WITH version_period AS (
    SELECT
        bom_id,
        version_id,
        start_date,
        end_date,
        FORMAT(end_date, 'yyyy-MM') AS year_month,
        version_date
    FROM source_bom_version
    WHERE bom_id IN (:supported_bom_ids)
), latest_version AS (
    SELECT
        *,
        MAX(version_date) OVER (PARTITION BY year_month) AS latest_version_date
    FROM version_period
)
SELECT
    year_month,
    bom_id,
    version_id
FROM latest_version
WHERE version_date = latest_version_date;
