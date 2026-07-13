
  
    

  create  table "nyc_taxi"."gold"."dim_time__dbt_tmp"
  
  
    as
  
  (
    -- Dimension model: dim_time
-- Chi tiết hóa thời gian đón khách từ stg_trips



SELECT DISTINCT
    tpep_pickup_datetime AS datetime_id,
    EXTRACT(YEAR FROM tpep_pickup_datetime) AS year,
    EXTRACT(MONTH FROM tpep_pickup_datetime) AS month,
    EXTRACT(DAY FROM tpep_pickup_datetime) AS day,
    EXTRACT(HOUR FROM tpep_pickup_datetime) AS hour,
    EXTRACT(DOW FROM tpep_pickup_datetime) AS day_of_week,
    TO_CHAR(tpep_pickup_datetime, 'FMDay') AS day_name,
    CASE 
        WHEN EXTRACT(DOW FROM tpep_pickup_datetime) IN (0, 6) THEN TRUE 
        ELSE FALSE 
    END AS is_weekend
FROM "nyc_taxi"."gold"."stg_trips"
  );
  