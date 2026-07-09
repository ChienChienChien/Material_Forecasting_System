SELECT
    purchase_order_line_key AS purchase_order_key,
    CAST(planned_receiving_date AS DATE) AS receiving_date,
    planned_receiving_qty_mt,
    COALESCE(actual_receiving_qty_mt, 0) AS actual_receiving_qty_mt
FROM source_procurement_receiving_schedule;
