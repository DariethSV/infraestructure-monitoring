CREATE EXTERNAL TABLE IF NOT EXISTS prometheus_metrics.metrics_curated (
    collected_at    STRING,
    labels_json     STRING,
    timestamp_unix  DOUBLE,
    value           DOUBLE
)
PARTITIONED BY (
    year        INT,
    month       INT,
    day         INT,
    metric_name STRING
)
STORED AS PARQUET
LOCATION 's3://infrastucture-vbenitezz-dfsanchezv/curated/prometheus/'
TBLPROPERTIES ('parquet.compress'='SNAPPY');