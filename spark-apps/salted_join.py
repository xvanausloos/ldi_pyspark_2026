from pyspark.sql import SparkSession
from pyspark.sql.functions import rand, floor, explode, array, lit

spark = SparkSession.builder \
    .appName("SaltedJoin") \
    .getOrCreate()

N_SALT = 10

sales = spark.read.parquet("/data/sales") \
    .withColumnRenamed("id","customer_id")

customers = spark.range(0,100000) \
    .withColumnRenamed("id","customer_id")

sales_salted = sales.withColumn(
    "salt",
    floor(rand()*N_SALT)
)

customers_salted = customers.withColumn(
    "salt",
    explode(array(*[lit(i) for i in range(N_SALT)]))
)

joined = sales_salted.join(
    customers_salted,
    ["customer_id","salt"]
)

print(joined.count())

# keep alive the Spark Application UI
input("Press Enter to stop Spark and close the application UI...")
spark.stop()