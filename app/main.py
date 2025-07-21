from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, student, user
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from app.core.metrics import REQUEST_COUNT, RESPONSE_TIME, ERROR_COUNT

app = FastAPI(
    title="Student Management API",
    description="API for managing student information and authentication",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(student.router, prefix="/students", tags=["Students"])
app.include_router(user.router, prefix="/user", tags=["User"])


# Middleware para registrar métricas
@app.middleware("http")
async def record_metrics(request, call_next):
    method = request.method
    endpoint = request.url.path

    # Registrar la hora de inicio para medir el tiempo de respuesta
    start_time = time.time()

    # Continuar con la solicitud
    response = await call_next(request)

    # Medir tiempo de respuesta
    duration = time.time() - start_time
    RESPONSE_TIME.labels(method=method, endpoint=endpoint).observe(duration)

    # Incrementar contador de peticiones
    REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()

    # Si hay un error (código de estado >= 400), aumentar el contador de errores
    if response.status_code >= 400:
        ERROR_COUNT.labels(method=method, endpoint=endpoint).inc()

    return response

# Ruta para exponer las métricas en formato Prometheus
@app.get("/metrics")
async def metrics():
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)

@app.get("/")
async def root():
    """
    Root endpoint that returns a welcome message.
    """
    return {
        "message": "Welcome to the Student Management API",
        "docs_url": "/docs",
        "redoc_url": "/redoc"
    }
