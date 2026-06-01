from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api import endpoints
from app.api.deps import HTTPClientProvider
from app.db.database import async_engine, Base

# The lifespan context manager guarantees this runs before any requests are accepted
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---
    print("\n[System] Initializing Database...")
    async with async_engine.begin() as conn:
        # Drop existing tables to clear corrupted states, then recreate them
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("[System] SQLite Telemetry DB initialized and tables created successfully.")
    
    # Yield control back to FastAPI to start accepting HTTP requests
    yield
    
    # --- SHUTDOWN LOGIC ---
    print("\n[System] Shutting down backend services...")
    await HTTPClientProvider.close_client()
    await async_engine.dispose()
    print("[System] Connection pools closed cleanly.")

# Instantiate the application with the lifespan manager
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the router
app.include_router(endpoints.router, prefix=settings.API_V1_STR, tags=["Generation Engine"])

@app.get("/", tags=["Health Check"])
async def root_health_check():
    return {
        "status": "healthy",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION
    }