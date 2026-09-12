from groq import Groq
from app.integrations.llm.models import SIMQueryIntent

class GroqLLMClient:
    MODEL = "openai/gpt-oss-20b"

    def __init__(self) -> None:
        self._client = Groq()

    def generate(self, prompt: str) -> str:
        response = self._client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você auxilia na análise de dados públicos "
                        "do Sistema Único de Saúde brasileiro."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        content = response.choices[0].message.content

        if content is None:
            raise RuntimeError("The LLM returned an empty response.")

        return content

    def interpret_sim_question(self, question: str) -> SIMQueryIntent:
        response = self._client.chat.completions.create(
            model=self.MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Converta perguntas sobre estatísticas do SIM em uma "
                        "instrução estruturada. "
                        "Use total_records para perguntas sobre o total de registros; "
                        "deaths_by_sex para agrupamentos por sexo; "
                        "e deaths_by_state para agrupamentos por UF. "
                        "Use descending para perguntas sobre maiores valores, "
                        "ascending para menores valores e none quando não houver "
                        "ordenação. O limite indica quantos resultados retornar."
                    ),
                },
                {
                    "role": "user",
                    "content": question,
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "sim_query_intent",
                    "strict": True,
                    "schema": SIMQueryIntent.model_json_schema(),
                },
            },
        )

        content = response.choices[0].message.content

        if content is None:
            raise RuntimeError("The LLM returned an empty response.")

        return SIMQueryIntent.model_validate_json(content)