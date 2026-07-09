WITH consumption AS (
    SELECT
        heat_no,
        material_id,
        secondary_furnace_no,
        weight_kg / 1000.0 AS weight_mt
    FROM source_actual_material_consumption
), heat_calendar AS (
    SELECT
        heat_no,
        CAST(furnace_start_datetime AS DATE) AS production_date
    FROM source_heat_calendar
)
SELECT
    c.heat_no,
    c.material_id,
    c.secondary_furnace_no,
    c.weight_mt,
    h.production_date
FROM consumption c
LEFT JOIN heat_calendar h
    ON c.heat_no = h.heat_no
WHERE h.production_date >= :start_date;
