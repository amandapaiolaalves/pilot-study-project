import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from app.collectors.sim import SIMCollector
from app.extractors.sim import SIMExtractor
from app.processors.sim import SIMProcessor
from app.services.sim import SIMService
from pydantic import BaseModel, Field

from app.integrations.llm.groq_client import GroqLLMClient
from app.services.sim_query import SIMQueryService


class SIMQuestionRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)

llm_client = GroqLLMClient()
query_service = SIMQueryService()

def get_llm_client() -> GroqLLMClient:
    return llm_client

def get_sim_query_service() -> SIMQueryService:
    return query_service


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

@router.post("/statistics/{job_id}/query")
def query_statistics(
    job_id: str,
    request: SIMQuestionRequest,
    service: SIMService = Depends(get_sim_service),
    llm_client: GroqLLMClient = Depends(get_llm_client),
    query_service: SIMQueryService = Depends(get_sim_query_service),
):
    try:
        job = service.get_statistics(job_id)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail="Statistics job not found.",
        )

    if job["status"] != "completed":
        raise HTTPException(
            status_code=409,
            detail=f"Statistics job is {job['status']}.",
        )

    intent = llm_client.interpret_sim_question(request.question)

    result = query_service.execute(
        statistics=job["result"],
        intent=intent,
    )

    return {
        "question": request.question,
        "intent": intent.model_dump(),
        "result": result,
    }

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