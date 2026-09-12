from app.integrations.llm.groq_client import GroqLLMClient
from app.services.sim_query import SIMQueryService


fake_statistics = {
    "total_records": 1_000,
    "deaths_by_sex": {
        "1": 550,
        "2": 450,
    },
    "deaths_by_state": {
        "SP": 400,
        "RJ": 250,
        "MG": 350,
    },
}

llm_client = GroqLLMClient()
query_service = SIMQueryService()

question = "Quais são os dois estados com mais óbitos?"

intent = llm_client.interpret_sim_question(question)
result = query_service.execute(fake_statistics, intent)

print("Intent:", intent.model_dump())
print("Result:", result)