from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SIMQueryIntent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    statistic: Literal[
        "total_records",
        "deaths_by_sex",
        "deaths_by_state",
    ]

    order: Literal[
        "none",
        "ascending",
        "descending",
    ]

    limit: int = Field(ge=1, le=27)