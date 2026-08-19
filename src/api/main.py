"""
FastAPI Main Application — Sprint 6 Day 38.

Central API application with 8 routers, CORS middleware,
request logging, and SQLite connection helpers.
"""

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


from src.api.routers import (
    health,
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)

_start_time = time.time()


def get_uptime() -> float:
    """Returns server uptime in seconds."""
    return round(time.time() - _start_time, 2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle events."""
    logger.info("FastAPI server starting up...")
    yield
    logger.info("FastAPI server shutting down...")


app = FastAPI(
    title="Nifty 100 Financial Intelligence Platform API",
    description="RESTful API for India's Nifty 100 companies — financials, screener, peers, valuation, clustering, and tearsheets.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS Middleware ───────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Logging Middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    elapsed_ms = round((time.time() - start) * 1000, 1)
    logger.info("%s %s -> %d (%sms)", request.method, request.url.path, response.status_code, elapsed_ms)
    return response


# ── Register Routers ─────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(health.router, prefix=PREFIX, tags=["Health"])
app.include_router(companies.router, prefix=PREFIX, tags=["Companies"])
app.include_router(screener.router, prefix=PREFIX, tags=["Screener"])
app.include_router(sectors.router, prefix=PREFIX, tags=["Sectors"])
app.include_router(peers.router, prefix=PREFIX, tags=["Peers"])
app.include_router(valuation.router, prefix=PREFIX, tags=["Valuation"])
app.include_router(portfolio.router, prefix=PREFIX, tags=["Portfolio"])
app.include_router(documents.router, prefix=PREFIX, tags=["Documents"])


# ── Root Redirect ─────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {"message": "Nifty100 Financial Intelligence API v1.0", "docs": "/docs"}
