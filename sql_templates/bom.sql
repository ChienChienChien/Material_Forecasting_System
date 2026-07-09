SELECT
    process_stage,
    material_id,
    steel_grade,
    unit_qty_kg_per_mt,
    CONCAT(steel_grade, '-', process_stage) AS steel_process_key
FROM source_bom
WHERE bom_id = :bom_id
  AND version_id = :version_id
  AND process_stage IN ('process_2', 'process_3');
