from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("JoinSkew") \
    .getOrCreate()

sales = spark.read.parquet("/data/sales")

customers = spark.range(0,100000) \
    .withColumnRenamed("id","customer_id")

joined = sales.join(
    customers,
    sales.id == customers.customer_id,
    "left"
)

print(joined.count())

# keep alive the Spark Application UI
input("Press Enter to stop Spark and close the application UI...")
spark.stop()