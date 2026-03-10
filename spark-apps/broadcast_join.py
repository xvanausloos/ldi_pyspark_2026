from pyspark.sql import SparkSession
from pyspark.sql.functions import broadcast

spark = SparkSession.builder \
    .appName("BroadcastJoin") \
    .getOrCreate()

sales = spark.read.parquet("/data/sales")

customers = spark.range(0,100000) \
    .withColumnRenamed("id","customer_id")

joined = sales.join(
    broadcast(customers),
    sales.id == customers.customer_id
)

print(joined.count())

# keep alive the Spark Application UI
input("Press Enter to stop Spark and close the application UI...")

spark.stop()