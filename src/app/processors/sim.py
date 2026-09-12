import json
import logging
from dataclasses import dataclass
from pathlib import Path
from queue import Queue
from threading import Event, Lock, Thread
from uuid import uuid4

import pandas as pd


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SIMJob:
    job_id: str
    csv_file: Path
    result_file: Path


class SIMProcessor:
    def __init__(self, chunk_size: int = 100_000):
        self.chunk_size = chunk_size
        self._queue: Queue[SIMJob | None] = Queue()
        self._jobs: dict[str, dict] = {}
        self._jobs_lock = Lock()
        self._stop_event = Event()
        self._worker: Thread | None = None

    def start(self) -> None:
        if self._worker and self._worker.is_alive():
            return

        self._stop_event.clear()
        self._worker = Thread(
            target=self._process_jobs,
            name="sim-processor",
            daemon=True,
        )
        self._worker.start()
        logger.info("SIM worker started")

    def stop(self) -> None:
        if not self._worker:
            return

        self._stop_event.set()
        self._queue.put(None)
        self._worker.join(timeout=5)
        self._worker = None
        logger.info("SIM worker stopped")

    def enqueue(self, csv_file: Path, result_dir: Path) -> dict:
        job_id = str(uuid4())
        job = SIMJob(
            job_id=job_id,
            csv_file=csv_file,
            result_file=result_dir / f"statistics-{job_id}.json",
        )

        with self._jobs_lock:
            self._jobs[job_id] = {"status": "queued"}

        self._queue.put(job)
        logger.info(
            "SIM statistics job queued",
            extra={"job_id": job_id, "csv_file": str(csv_file)},
        )
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> dict:
        with self._jobs_lock:
            job = self._jobs.get(job_id)

            if job is None:
                raise KeyError(job_id)

            result = None
            result_file = job.get("result_file")
            if result_file:
                result = json.loads(Path(result_file).read_text(encoding="utf-8"))

            response = {"job_id": job_id, **job}
            if result is not None:
                response["result"] = result
            return response

    def _process_jobs(self) -> None:
        while not self._stop_event.is_set():
            job = self._queue.get()

            if job is None:
                self._queue.task_done()
                break

            self._update_job(job.job_id, status="processing")
            logger.info(
                "SIM statistics job processing",
                extra={"job_id": job.job_id},
            )
            try:
                result = self.statistics(job.csv_file)
                job.result_file.parent.mkdir(parents=True, exist_ok=True)
                temporary_file = job.result_file.with_suffix(".json.tmp")
                temporary_file.write_text(
                    json.dumps(result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                temporary_file.replace(job.result_file)
                self._update_job(
                    job.job_id,
                    status="completed",
                    result_file=str(job.result_file),
                )
                logger.info(
                    "SIM statistics job completed",
                    extra={"job_id": job.job_id},
                )
            except Exception as error:
                self._update_job(
                    job.job_id,
                    status="failed",
                    error=str(error),
                )
                logger.exception(
                    "SIM statistics job failed",
                    extra={"job_id": job.job_id},
                )
            finally:
                self._queue.task_done()

    def _update_job(self, job_id: str, **updates) -> None:
        with self._jobs_lock:
            self._jobs[job_id].update(updates)

    def statistics(self, csv_file: Path) -> dict:
        logger.info(
            "SIM statistics calculation started",
            extra={"csv_file": str(csv_file)},
        )
        total_records = 0
        deaths_by_sex = {}
        deaths_by_state = {}

        for chunk in pd.read_csv(
            csv_file,
            sep=";",
            chunksize=self.chunk_size,
            encoding="latin1",
        ):
            total_records += len(chunk)

            if "SEXO" in chunk.columns:
                sex_counts = chunk["SEXO"].value_counts()

                for sex, count in sex_counts.items():
                    deaths_by_sex[str(sex)] = (
                        deaths_by_sex.get(str(sex), 0) + int(count)
                    )

            if "UF" in chunk.columns:
                state_counts = chunk["UF"].value_counts()

                for state, count in state_counts.items():
                    deaths_by_state[str(state)] = (
                        deaths_by_state.get(str(state), 0) + int(count)
                    )

        result = {
            "total_records": total_records,
            "deaths_by_sex": deaths_by_sex,
            "deaths_by_state": deaths_by_state,
        }
        logger.info(
            "SIM statistics calculation completed",
            extra={"csv_file": str(csv_file), "total_records": total_records},
        )
        return result
