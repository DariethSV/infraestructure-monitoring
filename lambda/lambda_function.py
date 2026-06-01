import json
import urllib.request
import boto3
from datetime import datetime, timezone

# Métricas que Lambda extrae de Prometheus
METRICS = [
    # CPU
    "node_cpu_seconds_total",
    # RAM
    "node_memory_MemAvailable_bytes",
    "node_memory_MemTotal_bytes",
    # RED
    "node_network_receive_bytes_total",
    "node_network_transmit_bytes_total",
    # DISCO
    "node_filesystem_avail_bytes",
    "node_filesystem_size_bytes",
    # PODS
    "kube_pod_status_phase",
    "kube_pod_container_resource_requests",
]

PROMETHEUS_URL = "http://k8s-monitori-promethe-3326bc4452-3c21ea83ae22b3d0.elb.us-east-1.amazonaws.com:9090"
BUCKET         = "infrastucture-vbenitezz-dfsanchezv"
PREFIX         = "raw/prometheus"

s3 = boto3.client("s3")


def query_prometheus(metric: str) -> list:
    url = f"{PROMETHEUS_URL}/api/v1/query?query={metric}"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", {}).get("result", [])
    except Exception as e:
        print(f"[ERROR] No se pudo obtener {metric}: {e}")
        return []


def lambda_handler(event, context):
    now        = datetime.now(timezone.utc)
    timestamp  = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    date_path  = now.strftime("year=%Y/month=%m/day=%d/hour=%H")

    collected = {}
    for metric in METRICS:
        results = query_prometheus(metric)
        collected[metric] = results
        print(f"[OK] {metric}: {len(results)} series")

    payload = {
        "collected_at": now.isoformat(),
        "metrics":      collected,
    }

    key = f"{PREFIX}/{date_path}/metrics_{timestamp}.json"
    s3.put_object(
        Bucket      = BUCKET,
        Key         = key,
        Body        = json.dumps(payload, ensure_ascii=False),
        ContentType = "application/json",
    )

    print(f"[OK] Guardado en s3://{BUCKET}/{key}")
    return {"statusCode": 200, "key": key}