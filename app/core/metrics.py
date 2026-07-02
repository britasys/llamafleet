from prometheus_client import Counter, Histogram, generate_latest

REQUESTS = Counter("llama_gateway_requests_total", "Total requests", ["endpoint", "backend", "status"])
LATENCY = Histogram("llama_gateway_request_latency_seconds", "Request latency", ["endpoint", "backend"])


def render_metrics() -> bytes:
    return generate_latest()
