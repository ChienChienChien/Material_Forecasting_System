SELECT
    material_id,
    material_name,
    storage_location,
    ending_inventory_mt,
    control_flag,
    quality_status
FROM source_inventory_lot_detail
WHERE control_flag = 'Y';
