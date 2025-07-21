from prometheus_client import Counter, Histogram

# Contador de peticiones HTTP
REQUEST_COUNT = Counter(
    "http_requests_total", 
    "Total HTTP requests", 
    ["method", "endpoint"]
)

# Histograma para medir la latencia (tiempos de respuesta)
RESPONSE_TIME = Histogram(
    "http_request_duration_seconds", 
    "HTTP request duration in seconds", 
    ["method", "endpoint"]
)

# Contador de errores por endpoint
ERROR_COUNT = Counter(
    "http_errors_total", 
    "Total HTTP errors", 
    ["method", "endpoint"]
)
