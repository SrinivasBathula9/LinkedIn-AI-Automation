from contextlib import asynccontextmanager
import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import asyncio

if sys.platform == "win32":
    # Force Proactor event loop for Playwright on Windows (Uvicorn defaults to Selector)
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    # Monkey patch to handle uvicorn's explicit override
    asyncio.WindowsSelectorEventLoopPolicy = asyncio.WindowsProactorEventLoopPolicy

from backend.config import settings
from backend.db.session import engine
from backend.api.routes import campaigns, stats, profiles, logs
from backend.api import websocket

log = structlog.get_logger()

# Optional imports — gracefully skip if not installed
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    _prometheus = True
except ImportError:
    _prometheus = False
    log.warning("prometheus_fastapi_instrumentator not installed — metrics disabled")

try:
    from backend.scheduler.scheduler import start_scheduler, stop_scheduler
    _scheduler = True
except ImportError as e:
    _scheduler = False
    log.warning("Scheduler dependencies not available", error=str(e))


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Starting LinkedIn Automation API", env=settings.app_env)
    if _scheduler:
        start_scheduler()
    yield
    if _scheduler:
        stop_scheduler()
    await engine.dispose()
    log.info("Shutdown complete")


app = FastAPI(
    title="LinkedIn Automation API",
    version="1.0.0",
    description="AI-driven LinkedIn connection request automation",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics (optional)
if _prometheus:
    Instrumentator().instrument(app).expose(app)

# Routers
app.include_router(campaigns.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(profiles.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(websocket.router)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}
