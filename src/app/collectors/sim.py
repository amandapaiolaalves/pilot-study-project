from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import sleep

import httpx


class SIMCollector:
    URL = (
        "https://s3.sa-east-1.amazonaws.com/"
        "ckan.saude.gov.br/SIM/csv/DO24OPEN_csv.zip"
    )
    FILENAME = "DO24OPEN_csv.zip"

    def __init__(
        self,
        output_dir: Path,
        max_retries: int = 3,
        max_age_hours: int = 24,
    ):
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.max_age = timedelta(hours=max_age_hours)

    def collect(self, update) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)

        output_file = self.output_dir / self.FILENAME

        if not update and self._is_recent(output_file):
            return output_file

        temp_file = output_file.with_suffix(".zip.tmp")

        for attempt in range(1, self.max_retries + 1):
            try:
                self._download(temp_file)

                temp_file.replace(output_file)

                return output_file

            except httpx.HTTPError:
                temp_file.unlink(missing_ok=True)

                if attempt == self.max_retries:
                    raise

                sleep(2 ** (attempt - 1))

        raise RuntimeError("Download failed")

    def _is_recent(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False

        modified_at = datetime.fromtimestamp(
            file_path.stat().st_mtime,
            tz=timezone.utc,
        )

        now = datetime.now(timezone.utc)

        return now - modified_at < self.max_age

    def _download(self, output_file: Path) -> None:
        timeout = httpx.Timeout(
            connect=10.0,
            read=60.0,
            write=60.0,
            pool=10.0,
        )

        with httpx.stream(
            "GET",
            self.URL,
            follow_redirects=True,
            timeout=timeout,
        ) as response:
            response.raise_for_status()

            with output_file.open("wb") as file:
                for chunk in response.iter_bytes():
                    file.write(chunk)