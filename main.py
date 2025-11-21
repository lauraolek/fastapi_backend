from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import estnltk_endpoint
from contextlib import asynccontextmanager

# --- Configuration ---
origins: List[str] = [
    "*",
    # "http://localhost:8080",
]

# --- Lifecycle Management (For future-proofing) ---
# Use an async context manager to handle startup/shutdown events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Optional: Perform heavy initialization like loading large NLP models here.
    print("Application Startup.")
    yield
    # Optional: Perform cleanup/closing connections here.
    print("Application Shutdown: Resources released.")

# --- FastAPI Initialization ---
# Initialize the application instance with metadata and the lifespan manager.
app = FastAPI(
    title="Estonian Morphology API",
    description="API for converting Estonian sentences based on the 'Ma tahan' ('I want') structure using EstNLTK.",
    version="1.0.0",
    lifespan=lifespan,
)

# --- ADD CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,             # Allow cookies and authentication headers
    allow_methods=["*"],                # Allow all HTTP methods (POST, GET, etc.)
    allow_headers=["*"],
)

# --- Include Routers ---
# This is how you integrate endpoints from different files/modules.
# All routes in morphology.py will be prefixed by /api/v1/morphology
app.include_router(estnltk_endpoint.router, prefix="/api/v1/estnltk", tags=["estnltk"])


# --- Root Endpoint (Health Check / Documentation Index) ---
@app.get("/", tags=["root"])
def read_root():
    """
    A simple root endpoint directing users to the API documentation.
    """
    return {
        "message": "Welcome to the Estonian Morphology API.", 
        "docs": "See /docs for the OpenAPI documentation (Swagger UI)."
    }