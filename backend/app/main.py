import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.integrity import router as integrity_router
from app.api.negotiations import router as negotiations_router
from app.api.purchase_requests import router as purchase_requests_router
from app.core.config import get_settings

settings = get_settings()
logging.basicConfig(level=settings.log_level)


@asynccontextmanager
async def lifespan(_: FastAPI):
    yield


app = FastAPI(title="CHOAM", version="0.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Idempotency-Key"],
)
app.include_router(health_router, prefix=settings.api_v1_prefix)
app.include_router(purchase_requests_router, prefix=settings.api_v1_prefix)
app.include_router(negotiations_router, prefix=settings.api_v1_prefix)
app.include_router(integrity_router, prefix=settings.api_v1_prefix)


@app.exception_handler(Exception)
async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logging.getLogger(__name__).exception("Unhandled application error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
