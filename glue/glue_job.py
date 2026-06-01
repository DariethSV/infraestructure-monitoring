import sys
from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import *

args = getResolvedOptions(sys.argv, ["JOB_NAME", "source_path", "dest_path"])

sc   = SparkContext()
glue = GlueContext(sc)
spark = glue.spark_session

SOURCE = args["source_path"]  
DEST   = args["dest_path"]    

# ── Leer JSONs del Raw ────────────────────────────────────
df_raw = spark.read.option("multiline", "true").json(SOURCE)

# ── Explotar métricas anidadas ────────────────────────────
# Cada métrica viene como dict: {"metric": {...labels}, "value": [timestamp, valor]}
metrics_to_process = [
    "node_cpu_seconds_total",
    "node_memory_MemAvailable_bytes",
    "node_memory_MemTotal_bytes",
    "node_network_receive_bytes_total",
    "node_network_transmit_bytes_total",
    "node_filesystem_avail_bytes",
    "node_filesystem_size_bytes",
    "kube_pod_status_phase",
]

dfs = []
for metric_name in metrics_to_process:
    df_metric = (
        df_raw
        .select(
            F.col("collected_at"),
            F.explode(F.col(f"metrics.{metric_name}")).alias("entry")
        )
        .select(
            F.col("collected_at"),
            F.lit(metric_name).alias("metric_name"),
            F.to_json(F.col("entry.metric")).alias("labels_json"),
            F.col("entry.value").getItem(0).cast("double").alias("timestamp_unix"),
            F.col("entry.value").getItem(1).cast("double").alias("value"),
        )
    )
    dfs.append(df_metric)

from functools import reduce
df_final = reduce(lambda a, b: a.union(b), dfs)

# ── Agregar partición por fecha ───────────────────────────
df_final = (
    df_final
    .withColumn("collected_at", F.to_timestamp("collected_at"))
    .withColumn("year",  F.year("collected_at"))
    .withColumn("month", F.month("collected_at"))
    .withColumn("day",   F.dayofmonth("collected_at"))
)

(
    df_final
    .write
    .mode("append")
    .partitionBy("year", "month", "day", "metric_name")
    .parquet(DEST)
)

print(f"[OK] Curated escrito en {DEST}")