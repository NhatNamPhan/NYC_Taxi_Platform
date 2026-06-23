from pyspark.sql import SparkSession
import pyspark.sql.functions as F
import os
import sys

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    
    hadoop_home = os.path.join(project_root, "hadoop")
    os.environ["HADOOP_HOME"] = hadoop_home
    os.environ["PATH"] += os.pathsep + os.path.join(hadoop_home, "bin")
    
    spark = (SparkSession.builder
        .appName("NYC Taxi Bronze  to Silver")
        .master("local[*]")
        .config("spark.driver.memory", "8g")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.extraJavaOptions", "--add-opens=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED")
        .getOrCreate())
    

    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session đã được tạo khởi động thành công!")
    
    input_path = os.path.join(project_root, "data", "bronze")
    
    print(f"Đang đọc dữ liệu từ {input_path}")
    df = spark.read.parquet(input_path)
    
    print(f'Tổng số dòng đọc đươc từ Bronze: {df.count():,}')
    #df.printSchema()
    
    # 1. Chuẩn hóa mã vùng: nếu nằm ngoài khoảng [1, 265] thì đưa về NULL
    df_validated = df.withColumn(
        "PULocationID", 
        F.when((F.col("PULocationID") >= 1) & (F.col("PULocationID") <= 265), F.col("PULocationID")).otherwise(F.lit(None))
    ).withColumn(
        "DOLocationID",
        F.when((F.col("DOLocationID") >= 1) & (F.col("DOLocationID") <= 265), F.col("DOLocationID")).otherwise(F.lit(None))
    )

    # 2. Điều kiện lọc loại bỏ các dòn bị lỗi (Outliers)
    cleaned_condition = (
        (F.col("trip_distance") > 0) & (F.col("trip_distance") <= 500) &
        (F.col("fare_amount") > 0) & (F.col("fare_amount") < 1000) &
        (F.col("passenger_count") >= 1) & (F.col("passenger_count") <= 8) &
        (F.col("tip_amount") >= 0) &
        (F.col("tpep_pickup_datetime").isNotNull())        
    )
    
    df_cleaned = df_validated.filter(cleaned_condition)
    
    # 3. Thống kê số lượng dòng bị lọc
    total_cleaned_rows = df_cleaned.count()
    dropped_rows = df.count() - total_cleaned_rows
    print(f"Số lượng dòng bị loại bỏ: {dropped_rows:,}")
    print(f"Số lượng dòng còn lại đưa vào Bronze: {total_cleaned_rows:,}")
    
    # 4. Ghi dữ liệu đã làm sạch vào thư mục Silver với phân vùng year/month
    output_path = os.path.join(project_root, "data", "silver")
    print(f"Đang ghi dữ liệu Silver vào {output_path}")

    df_cleaned.repartition("year", "month").write\
        .mode("overwrite") \
        .partitionBy("year", "month") \
        .parquet(output_path)
    
    
    print("Ghi dữ liệu vào Silver hoàn tất!")        
    spark.stop()
    
if __name__ == "__main__":
    main()