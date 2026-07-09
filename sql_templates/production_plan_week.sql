WITH latest_plan AS (
    SELECT
        *,
        MAX(data_date) OVER (PARTITION BY year_month, week_no) AS latest_data_date
    FROM source_weekly_production_plan
)
SELECT
    year_month,
    week_no,
    steel_grade,
    process_2_qty,
    process_3_qty,
    total_planned_qty
FROM latest_plan
WHERE data_date = latest_data_date
  AND year_month = :year_month
  AND total_planned_qty <> 0;
