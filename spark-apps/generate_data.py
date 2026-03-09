from pyspark.sql import SparkSession
from pyspark.sql.functions import rand, when

spark = SparkSession.builder \
    .appName("GenerateSkewData") \
    .getOrCreate()

n_rows = 20_000_000

df = spark.range(0, n_rows)

df = df.withColumn("amount", (rand()*100).cast("int"))

df = df.withColumn(
    "country",
    when(rand() < 0.85, "FR")
    .when(rand() < 0.10, "US")
    .otherwise("UK")
)

df.write.mode("overwrite").parquet("/data/sales")

spark.stop()