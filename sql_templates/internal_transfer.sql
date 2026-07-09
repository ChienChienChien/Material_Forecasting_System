SELECT
    CAST(transfer_date AS DATE) AS transfer_date,
    material_id,
    SUM(net_weight_mt) AS net_weight_mt
FROM source_internal_material_transfer
WHERE transfer_status = 'confirmed'
  AND transfer_date >= :start_date
GROUP BY CAST(transfer_date AS DATE), material_id;
