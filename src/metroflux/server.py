from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

import os

from metroflux.services.agent_services.agent_executor_factory import AgentExecuterFactory
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
factory = AgentExecuterFactory()

class QueryRequest(BaseModel):
    query: str

executor = factory.create_agent_executer(
        thread_id="thread_1",
        model_name=os.getenv("model_name"),
        model_provider=os.getenv("model_provider")
    )

print("model used:",os.getenv("model_name")," provider:",os.getenv("model_provider"))
@app.post("/query")
def run_agent(request: QueryRequest):
    result = executor.invoke(user_query=request.query)
    return {
        "output_text": result.summary,
        "graph_needed": result.is_graph_needed,
        "graph_json": result.graph_json,
    }

def api() -> None:
    global executor

    uvicorn.run("metroflux.server:app", host="127.0.0.1", port=8000,reload=True)


if __name__ == "__main__":
    api()