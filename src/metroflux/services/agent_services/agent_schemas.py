from pydantic import BaseModel
from typing import Annotated
class AgentState(BaseModel):
    user_query: str
    is_graph_needed: bool
    graph_instructions: str
    graph_json: str
    output_text: str
    retry_count: int


class GraphResponse(BaseModel):
    graph_code: Annotated[
        str, "the python plotly graph code for the provided instructions"
    ]

