import os
import sys
from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from dotenv import load_dotenv

def main():
    load_dotenv()
    # 1. Tự động xác định project root và cấu hình  HADOOP HOME cho Windows
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    hadoop_home = os.path.join(project_root, "hadoop")
    os.environ["HADOOP_HOME"] = hadoop_home
    os.environ["PATH"] += os.pathsep + os.path.join(hadoop_home, "bin")
    
    # 2. Khởi động Spark Session với cấu hình tối ưu 8GB RAM
    spark = (SparkSession.builder
        .appName("NYC Taxi Silver to Gold")
        .config("spark.driver.memory", "8g")
        .config("spark.local.dir", "E:\\spark-temp")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.jars.packages", "org.postgresql:postgresql:42.7.3")
        .config("spark.driver.extraJavaOptions", "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED")
        .getOrCreate())
    
    # 3. Đọc dữ liệu từ Silver Layer
    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session cho Gold Layer đã được tạo khởi động thành công!")
    
    silver_path = os.path.join(project_root, "data", "silver")
    print(f"Đang đọc dữ liệu từ: {silver_path}")
    
    df_silver = spark.read.parquet(silver_path)
    print(f"Tổng số dòng đọc từ Silver {df_silver.count():,}")
    
    # 4. Đọc bảng danh mục Taxi Zone Lookup (CSV)
    zone_lookup_path = os.path.join(project_root, "data", "taxi_zone_lookup.csv")
    print(f"Đang đọc bảng danh mục từ: {zone_lookup_path}")
    
    zone_df = spark.read.option("header", "true").csv(zone_lookup_path)
    
    # 5. Thực hiện LEFT JOIN dữ liệu  Silver với bảng Zone Lookup theo PULocationID
    df_joined = df_silver.join(
        zone_df.alias("pickup_zone"),
        df_silver.PULocationID == F.col("pickup_zone.LocationID"),
        "left"
    ).withColumnRenamed("Zone", "pickup_zone_name") \
    .withColumnRenamed("Borough", "pickup_borough") \
    .drop("LocationID")
    
    # 6. Xem cấu trúc bảng và 5 dòng dữ liệu sau khi join
    # print("Schema của bảng sau khi Join:")
    # df_joined.printSchema()
    
    # print("5 dòng dữ liệu mẫu sau khi Join:")
    # df_joined.show(5)
    
    # 7. Tính toán các chỉ số nghiệp vụ mới
    df_metrics = df_joined.withColumn(
        # Tính thời gian đi (phút)
        "trip_duration_min",
        F.round((F.unix_timestamp("tpep_dropoff_datetime") - F.unix_timestamp("tpep_pickup_datetime")) / 60, 2)
    ).withColumn(
        # Tính tỉ lệ % tiền tiếp (Phòng tránh chia cho 0)
        "tip_percentage",
        F.round(
            F.when(F.col("fare_amount") > 0, (F.col("tip_amount") / F.col("fare_amount")) * 100)
            .otherwise(0), 2
        )
    ).withColumn(
        # Tính vận tốc trung bình (mph)
        "speed_mph",
        F.round(
            F.when(F.col("trip_duration_min") > 0, F.col("trip_distance") / (F.col("trip_duration_min") / 60))
            .otherwise(0), 2
        )
    ).withColumn(
        # Trích xuất các chiều thời gian
        "hour", F.hour(F.col("tpep_pickup_datetime")) 
    ).withColumn(
        "day_of_week", F.dayofweek(F.col("tpep_pickup_datetime"))
    )

    # 8. Xem cấu trúc bảng mới
    # print("Schema của Gold DataFrame sau khi tính toán:")
    # df_metrics.printSchema()
    # print("5 dòng dữ liệu mẫu:")
    # df_metrics.show(5)
    
    # 9.Ghi dữ liệu Gold ra thư mục local (Parquet)
    output_path = os.path.join(project_root, "data", "gold")
    print(f"Đang ghi dữ liệu Gold vào {output_path}...")
    
    df_metrics.repartition("year", "month").write \
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(output_path)
        
    print("Ghi dữ liệu Gold (Parquet) hoàn tất!")
    
    # 10. Nạp dữ liệu Gold vào PostgreSQL local JDBC sử dụng biến môi trường
    print("Đang nạp dữ liệu vào PostgreSQL local ...")
    
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5433")
    db_name = os.getenv("DB_NAME", "nyc_taxi")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD")
    
    jdbc_url = f"jdbc:postgresql://{db_host}:{db_port}/{db_name}"
    
    df_metrics.write \
        .format("jdbc") \
        .option("url", jdbc_url) \
        .option("dbtable", "gold.trips") \
        .option("user", db_user) \
        .option("password", db_password) \
        .option("driver", "org.postgresql.Driver") \
        .option("truncate", "true") \
        .mode("overwrite") \
        .save()

    
    print("Nạp dữ liệu vào PostgreSQL hoàn tất!!")
            
    spark.stop()
    
    
if __name__ == "__main__":
    main()
    