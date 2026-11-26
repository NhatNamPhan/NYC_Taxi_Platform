-- Hour grain: 24 rows, independent of fact volume.
SELECT hour AS hour_id, hour, LPAD(hour::TEXT, 2, '0') || ':00' AS hour_label
FROM GENERATE_SERIES(0, 23) AS hours(hour)
