from app.integrations.llm.models import SIMQueryIntent


class SIMQueryService:
    def execute(
        self,
        statistics: dict,
        intent: SIMQueryIntent,
    ) -> dict:
        selected_data = statistics[intent.statistic]

        if isinstance(selected_data, int):
            return {
                "statistic": intent.statistic,
                "items": [
                    {
                        "label": "total",
                        "value": selected_data,
                    }
                ],
            }

        items = [
            {
                "label": label,
                "value": value,
            }
            for label, value in selected_data.items()
        ]

        if intent.order != "none":
            items.sort(
                key=lambda item: item["value"],
                reverse=intent.order == "descending",
            )

        return {
            "statistic": intent.statistic,
            "items": items[:intent.limit],
        }