from pathlib import Path
from zipfile import ZipFile


class SIMExtractor:
    def extract(
        self,
        zip_file: Path,
        output_dir: Path,
    ) -> list[Path]:
        output_dir.mkdir(parents=True, exist_ok=True)

        with ZipFile(zip_file) as archive:
            archive.extractall(output_dir)

            return [
                output_dir / name
                for name in archive.namelist()
                if not name.endswith("/")
            ]