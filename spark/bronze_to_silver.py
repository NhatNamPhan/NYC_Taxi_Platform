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
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.driver.extraJavaOptions", "--add-open=java.base/sun.nio.ch=ALL-UNNAMED --add-opens=java.base/java.nio=ALL-UNNAMED")
        .getOrCreate())
    

    spark.sparkContext.setLogLevel("WARN")
    print("Spark Session đã được tạo khởi động thành công!")
    
    input_path = os.path.join(project_root, "data", "bronze")
    
    print(f"Đang đọc dữ liệu từ {input_path}")
    df = spark.read.parquet(input_path)
    
    print(f'Tổng số dòng đọc đươc từ Bronze: {df.count():,}')
    df.printSchema()
    spark.stop()
    
if __name__ == "__main__":
    main()