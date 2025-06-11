from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, student

app = FastAPI(
    title="Student Management API",
    description="API for managing student information and authentication",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(student.router, prefix="/students", tags=["Students"])

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
