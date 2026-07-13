import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_config
from app.database import engine, Base, SessionLocal
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.store import router as store_router
from app.routers.analytics import router as analytics_router
from app.services import auth_service, scheduler_service

config = get_config()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure data directories exist
    os.makedirs(config.DATA_DIR, exist_ok=True)
    os.makedirs(config.STORES_DIR, exist_ok=True)

    # Automatically create database tables if they do not exist
    # This acts as an initial bootstrap on PostgreSQL / SQLite
    Base.metadata.create_all(bind=engine)

    # Ensure super admin is created
    db = SessionLocal()
    try:
        auth_service.ensure_super_admin(db)
    except Exception as exc:
        print(f"Could not bootstrap super admin on startup: {exc}")
    finally:
        db.close()

    # Initialize the background scheduler
    scheduler_service.init_scheduler()

    yield

    # Shutdown scheduler on app exit
    scheduler = scheduler_service.get_scheduler()
    if scheduler:
        try:
            scheduler.shutdown()
        except Exception:
            pass


app = FastAPI(
    title="Assortment Dashboard API",
    version="3.0.0",
    lifespan=lifespan
)

# CORS configuration matching allowed origins from config
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])
app.include_router(store_router, prefix="/api/store", tags=["Store"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])


@app.get("/")
def index():
    return {
        "name": "Assortment Dashboard API",
        "version": "3.0.0",
        "status": "running",
        "docs": "/api/health",
    }
