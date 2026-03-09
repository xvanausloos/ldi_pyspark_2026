from pyspark.sql import SparkSession
from pyspark.sql.functions import sum

spark = SparkSession.builder \
    .appName("SkewGroupBy") \
    .config("spark.sql.shuffle.partitions", 12) \
    .getOrCreate()

df = spark.read.parquet("/data/sales")

result = df.groupBy("country").agg(
    sum("amount").alias("total")
)

result.show()

# keep alive the Spark Application UI
input("Press Enter to stop Spark and close the application UI...")
spark.stop()
