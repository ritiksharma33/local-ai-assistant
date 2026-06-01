from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import endpoints
from app.api.deps import HTTPClientProvider

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup behavior: The connection pool gets initialized when needed
    yield
    # Shutdown behavior: Clean up connections gracefully on server termination
    print("\nShutting down backend services... Closing connection pools.")
    await HTTPClientProvider.close_client()

# Instantiate the application with structured lifespan management
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS so your React application on localhost:5173 can access this API safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this to specific origins in a strict production cloud setup
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router under the production API version layout string (/api/v1)
app.include_router(endpoints.router, prefix=settings.API_V1_STR, tags=["Generation Engine"])

@app.get("/", tags=["Health Check"])
async def root_health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }