SELECT
    CAST(snapshot_datetime AS DATE) AS snapshot_date,
    material_id,
    material_name,
    ending_inventory_mt
FROM source_inventory_snapshot
WHERE snapshot_datetime >= DATEADD(MONTH, -2, CURRENT_DATE);
