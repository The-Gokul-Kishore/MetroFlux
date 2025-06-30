from pydantic import BaseModel,Field
from typing import Annotated,  Literal
from datetime import date



class RouterResponse(BaseModel):
    route: Literal[
        "weather_current",
        "weather_future",
        "weather_past",
        "weather_summary",
        "general",
    ]
    location: Annotated[str,"the location of the query if location based eg chennai India"]
    location_based: bool


class DateResponse(BaseModel):
    start_date: date = Field(..., description="ISO format: YYYY-MM-DD")
    end_date: date = Field(..., description="ISO format: YYYY-MM-DD")


class SummarizerResponse(BaseModel):
    summary: str
    is_graph_needed: bool
    graph_instructions: str


class GraphResponse(BaseModel):
    graph_code: Annotated[
        str, "the python plotly graph code for the provided instructions"
    ]

class FinalResponse(BaseModel):
    summary:str
    is_graph_needed:bool
    graph_json:str