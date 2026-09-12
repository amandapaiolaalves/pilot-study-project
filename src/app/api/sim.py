import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.collectors.sim import SIMCollector
from app.extractors.sim import SIMExtractor
from app.processors.sim import SIMProcessor
from app.services.sim import SIMService


router = APIRouter(
    prefix="/sim",
    tags=["SIM"],
)
logger = logging.getLogger(__name__)


RAW_DIR = Path("/home/mateus/PycharmProjects/pilot-study-project/src/app/collectors/data/raw/sim/2024/")
EXTRACTED_DIR = Path("/home/mateus/PycharmProjects/pilot-study-project/src/app/collectors/data/raw/sim/2024/")


collector = SIMCollector(
    output_dir=RAW_DIR,
)
extractor = SIMExtractor()
processor = SIMProcessor()
service = SIMService(
    collector=collector,
    extractor=extractor,
    processor=processor,
    raw_dir=RAW_DIR,
    extracted_dir=EXTRACTED_DIR,
)


def get_sim_service() -> SIMService:
    return service


def start_sim_processor() -> None:
    processor.start()


def stop_sim_processor() -> None:
    processor.stop()


@router.get("/status")
def get_status(
    service: SIMService = Depends(get_sim_service),
):
    return service.get_status()


@router.post("/collect")
def collect_data(
    service: SIMService = Depends(get_sim_service),
):
    logger.info("SIM data collection requested")
    return service.collect()


@router.put("/collect")
def collect_and_extract_data(
    service: SIMService = Depends(get_sim_service),
):
    logger.info("SIM data collection and extraction requested")
    collect_result = service.collect()
    service.extract()
    return collect_result


@router.get("/statistics/{job_id}")
def get_statistics_job(
    job_id: str,
    service: SIMService = Depends(get_sim_service),
):
    try:
        return service.get_statistics(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Statistics job not found.")


@router.post("/statistics", status_code=202)
def create_statistics_job(
    service: SIMService = Depends(get_sim_service),
):
    try:
        logger.info("SIM statistics job creation requested")
        return service.create_statistics_job()
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error))