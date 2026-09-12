from pathlib import Path

from app.collectors.sim import SIMCollector


def main():
    collector = SIMCollector(
        output_dir=Path("data/raw/sim/2024")
    )

    file_path = collector.collect()

    print(f"Arquivo coletado: {file_path}")


if __name__ == "__main__":
    main()