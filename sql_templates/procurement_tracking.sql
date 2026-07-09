WITH po_line AS (
    SELECT
        purchase_order_no,
        purchase_order_line_no,
        AVG(order_qty_mt) AS order_qty_mt,
        SUM(received_qty_mt) AS received_qty_mt,
        MAX(import_date) AS import_date,
        MAX(material_name) AS material_name,
        MAX(material_id) AS material_id,
        MAX(contract_delivery_date) AS contract_delivery_date,
        MAX(purchase_type) AS purchase_type
    FROM source_purchase_order_tracking
    WHERE is_deleted = 0
      AND created_at >= DATEADD(MONTH, -3, CURRENT_DATE)
    GROUP BY purchase_order_no, purchase_order_line_no
)
SELECT
    CONCAT(purchase_order_no, '-', LPAD(purchase_order_line_no, 5, '0')) AS main_key,
    purchase_order_no,
    COALESCE(received_qty_mt, order_qty_mt) AS net_weight_mt,
    material_name,
    material_id,
    CAST(import_date AS DATE) AS import_date,
    purchase_type,
    CAST(contract_delivery_date AS DATE) AS contract_delivery_date
FROM po_line;
