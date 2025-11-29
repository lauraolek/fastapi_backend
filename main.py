from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.endpoints import estnltk_endpoint
from api.endpoints import tts_endpoint
from contextlib import asynccontextmanager, AsyncExitStack
import httpx

# --- Configuration ---
origins: List[str] = [
    "*",
    # "http://localhost:8080",
]

# --- Lifecycle Management ---
# Use AsyncExitStack to manage multiple context managers gracefully
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with AsyncExitStack() as stack:
        # 1. Run the TTS service lifespan manager first
        await stack.enter_async_context(tts_endpoint.tts_lifespan_manager(app))
        print("Application Startup.")
        yield
    print("Application Shutdown: All resources released.")

# --- FastAPI Initialization ---
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
app.include_router(estnltk_endpoint.router, prefix="/api/v1/estnltk", tags=["estnltk"])
app.include_router(tts_endpoint.router, prefix="/api/v1/tts", tags=["tts"])


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