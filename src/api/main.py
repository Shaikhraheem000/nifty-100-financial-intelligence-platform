"""
Main FastAPI Application Entry Point for Nifty 100 Financial Intelligence Platform.
Exposes 16 REST endpoints with CORS, logging middleware, and OpenAPI documentation.
"""

import time
import logging
import json
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routers import (
    health,
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("api")

app = FastAPI(
    title="Nifty 100 Financial Intelligence Platform API",
    description="Production REST API providing access to financial statements, ratios, screener, peer percentiles, tearsheet downloads, and ML clustering.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/api/v1/openapi.json"
)

# CORS Middleware (Internal use - allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} - Status: {response.status_code} - Completed in {duration_ms}ms"
    )
    response.headers["X-Process-Time-Ms"] = str(duration_ms)
    return response


# Include Routers with /api/v1 Prefix
API_PREFIX = "/api/v1"
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(companies.router, prefix=API_PREFIX)
app.include_router(screener.router, prefix=API_PREFIX)
app.include_router(sectors.router, prefix=API_PREFIX)
app.include_router(peers.router, prefix=API_PREFIX)
app.include_router(valuation.router, prefix=API_PREFIX)
app.include_router(portfolio.router, prefix=API_PREFIX)
app.include_router(documents.router, prefix=API_PREFIX)


@app.get("/", tags=["Root"])
def root():
    """Root entry point directing users to OpenAPI documentation."""
    return {
        "platform": "Nifty 100 Financial Intelligence Platform",
        "version": "1.0.0",
        "documentation": "/docs",
        "api_v1_health": f"{API_PREFIX}/health"
    }


def export_openapi_spec(output_path=None):
    """Export the OpenAPI schema to docs/openapi.json and Postman Collection JSON."""
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    if output_path is None:
        output_path = os.path.join(base_dir, 'docs', 'openapi.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    openapi_schema = app.openapi()
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(openapi_schema, f, indent=2)
    print(f"Exported OpenAPI specification to {output_path}")

    # Build and export Postman Collection format
    postman_path = os.path.join(base_dir, 'docs', 'postman_collection.json')
    items = []
    for path, methods in openapi_schema.get("paths", {}).items():
        for method, details in methods.items():
            items.append({
                "name": details.get("summary", path),
                "request": {
                    "method": method.upper(),
                    "header": [],
                    "url": {
                        "raw": f"{{{{baseUrl}}}}{path}",
                        "host": ["{{baseUrl}}"],
                        "path": [p for p in path.strip("/").split("/") if p]
                    },
                    "description": details.get("description", "")
                }
            })

    postman_collection = {
        "info": {
            "name": "Nifty 100 Financial Intelligence API",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": items,
        "variable": [
            {
                "key": "baseUrl",
                "value": "http://localhost:8000",
                "type": "string"
            }
        ]
    }
    with open(postman_path, 'w', encoding='utf-8') as f:
        json.dump(postman_collection, f, indent=2)
    print(f"Exported Postman collection to {postman_path}")


if __name__ == "__main__":
    export_openapi_spec()
