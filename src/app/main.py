from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from app.api.sim import (
    router as sim_router,
    start_sim_processor,
    stop_sim_processor,
)
from app.logging_config import configure_logging


configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger = logging.getLogger(__name__)
    start_sim_processor()
    logger.info("SIM processor started")
    try:
        yield
    finally:
        stop_sim_processor()
        logger.info("SIM processor stopped")


app = FastAPI(
    title="Pilot Study Project",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


app.include_router(sim_router)