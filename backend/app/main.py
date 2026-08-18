from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.database import check_database_connection

app = FastAPI(
    title="SuperDocs Document Intelligence Platform",
    description="Agentic document analysis and workflow platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    database_healthy = check_database_connection()

    return {
        "status": "ok" if database_healthy else "degraded",
        "database": "connected" if database_healthy else "unavailable",
    }