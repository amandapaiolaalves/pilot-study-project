from pathlib import Path

from app.collectors.sim import SIMCollector
from app.extractors.sim import SIMExtractor
from app.processors.sim import SIMProcessor


class SIMService:
    def __init__(
        self,
        collector: SIMCollector,
        extractor: SIMExtractor,
        processor: SIMProcessor,
        raw_dir: Path,
        extracted_dir: Path,
    ):
        self.collector = collector
        self.extractor = extractor
        self.processor = processor
        self.raw_dir = raw_dir
        self.extracted_dir = extracted_dir

    @property
    def zip_file(self) -> Path:
        return self.raw_dir / "DO24OPEN_csv.zip"

    def get_status(self) -> dict:
        if not self.zip_file.exists():
            return {
                "exists": False,
                "file": self.zip_file.name,
            }

        return {
            "exists": True,
            "file": self.zip_file.name,
            "size": self.zip_file.stat().st_size,
        }

    def collect(self, update=False) -> dict:
        file_path = self.collector.collect(update)

        return {
            "status": "collected",
            "file": file_path.name,
            "size": file_path.stat().st_size,
        }

    def extract(self) -> dict:
        if not self.zip_file.exists():
            raise FileNotFoundError(
                "Error trying to extract SIM data from zip file."
            )

        files = self.extractor.extract(
            zip_file=self.zip_file,
            output_dir=self.extracted_dir,
        )

        return {
            "status": "extracted",
            "files": [str(file) for file in files],
        }

    def create_statistics_job(self) -> dict:
        csv_files = list(self.extracted_dir.glob("*.csv"))

        if not csv_files:
            raise FileNotFoundError(
                "SIM CSV file has not been extracted yet."
            )

        return self.processor.enqueue(
            csv_file=csv_files[0],
            result_dir=self.extracted_dir,
        )

    def get_statistics(self, job_id: str) -> dict:
        return self.processor.get_job(job_id)