import os
import sys
from pyspark.sql import SparkSession
import pyspark.sql.functions as F

def main():
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
        .config("spark.sql.session.timeZone", "UTC")
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
    print("Schema của bảng sau khi Join:")
    df_joined.printSchema()
    
    print("5 dòng dữ liệu mẫu sau khi Join:")
    df_joined.show(5)

    
    spark.stop()
    
    
if __name__ == "__main__":
    main()
    