from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool,Tool
from typing import List
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langchain_tavily import TavilySearch
from langchain.chat_models.base import BaseChatModel

from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv, find_dotenv
from typing import Annotated
import os
import requests
import getpass
from pydantic import BaseModel
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio


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


load_dotenv(r"D:\projects\climate\.env", override=True)


def exec_code(code):
    try:
        local_vars = {}
        exec(code, {"pd": pd, "px": px, "go": go, "pio": pio}, local_vars)
        return local_vars
    except Exception as e:
        print("Error in executing code:", e)
        raise e


def exec_and_validate(code):
    try:
        if "fig" not in code:
            raise Exception("fig not found in code")
        local_vars = exec_code(code)
        if "fig" not in local_vars:
            raise Exception("fig not found in code")
        fig = local_vars["fig"]
        fig_json = fig.to_json()
        return fig_json
    except Exception as e:
        print("Error in validating code:", e)
        raise e


print(find_dotenv())
if "GOOGLE_API_KEY" not in os.environ:
    os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter your Google AI API key: ")


memory = MemorySaver()
model = init_chat_model(
    model="llama-3.1-8b-instant",       
    model_provider="groq"          
)
search = TavilySearch(max_results=3)


@tool
def weather_current(lat: float, lon: float) -> dict:
    """
    Returns only current weather data.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


@tool
def weather_future(lat: float, lon: float,days: int=7) -> dict:
    """
    Returns only future forecast (hourly + daily).
    only up to 16 days in future
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "temperature_2m,precipitation",
        "daily": "temperature_2m_max,precipitation_sum",
        "forecast_days": days,
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


@tool
def weather_past(lat: float, lon: float, start_date: str, end_date: str) -> dict:
    """
    Returns historical reanalysis (hourly) from start_date to end_date.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,precipitation",
        "timezone": "auto",
    }
    return requests.get(url, params=params).json()


@tool
def weather_summary(
    lat: float, lon: float, start_date: str = None, end_date: str = None
) -> dict:
    """
    Returns:
      • Just current if no dates.
      • Future if start_date ≥ today.
      • Past if end_date ≤ today.
      • Both if range spans before and after today.
      only 16days to future but till 1940AD in past
    """
    from datetime import date

    today = date.today().isoformat()
    result = {}

    # 1. No dates → current only
    if not start_date and not end_date:
        result["current"] = weather_current(lat, lon)
        return result

    # 2. Future forecast
    if not start_date or start_date > today:
        result["future"] = weather_future(lat, lon)

    # 3. Historical data
    hist_start = start_date if start_date else today
    hist_end = min(end_date, today) if end_date else today
    if hist_start <= hist_end:
        result["past"] = weather_past(lat, lon, hist_start, hist_end)

    return result


tools = [search, weather_current, weather_future, weather_past, weather_summary]


def extract_field(data, field):
    try:
        return data[field]
    except Exception as e:
        raise Exception(f"Field '{field}' not found or not valid JSON: {e}")


def extract_json(text):
    start = "```json"
    end = "```"
    if start in text and end in text:
        raw_json = text.split(start)[1].split(end)[0].strip()
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON format: {e}")
    
    raise Exception("JSON block not found. Expected: ```json ... ```")

class MainAgent:
    def __init__(self,model:BaseChatModel,tools:List[Tool],memory:MemorySaver,thread_id:str):
        self.executor = create_react_agent(model=model, checkpointer=memory, tools=tools)
        self.config = {"configurable": {"thread_id": thread_id}}
        self.prompt_template = self._get_prompt_template()

    def _get_prompt_template(self):
                
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are a helpful weather assistant. Always use tools to answer  weather related queries. "
                    "if the user query is not related to weather, answer with following same json format (while answering trivial questions like 'hi') and push user to ask about weather'."
                    "Never guess or invent data."
                ),
                (
                    "user",
                    """Instructions:
            follow this plan:
        Given a user query, respond with a clear plan for handling it using the available tools.

        Use these steps:
        1. Use TavilySearch to get the latitude and longitude of the location.
        2. Choose one of the following tools and must call  it:
        - `weather_current` (for current weather)
        - `weather_future` (for forecasts)
        - `weather_past` (for historical data)
        - `weather_summary` (for date ranges spanning past and future)
        4. Visualization is STRONGLY ENCOURAGED if:
        - There are multiple data points (like hourly or daily readings).
        - The result spans more than one day.
        - The user asks for trends, forecasts, or comparisons.
        5. Graph instructions if needed should include all the infromation including data all step by step
            -data points in format of a dict
            -graph type
            -x axis (name and units)
            -y axis (name and units)
            -etc
        fromat so the final output after tool calls MUST contain:
        in JSON:

        {{
        "output_text": "...Your response be it weather or error or other information...",
        "is_graph_needed": true or false,
        "graph_instructions": "...describe chart or leave empty..."
        }}
        Here is the user query:
        {user_query}
        """
                ),
            ]
        )
        return prompt_template
    def invoke(self,state: AgentState)-> AgentState:
        query = state.user_query
        error_notes = "\n\n errors from previous attempts:"
        cnt = 0
        print("executing main_agent_call")
        while(cnt<=state.retry_count):
            try:
                prompt = self.prompt_template.invoke({"user_query": query+error_notes})

                output = self.executor.invoke(prompt, config=self.config)
                raw_ai_response = next((msg.content for msg in reversed(output["messages"]) if msg.type == "ai"), "")
                ai_response = extract_json(raw_ai_response)
                state.output_text = extract_field(ai_response, "output_text")
                state.graph_instructions = extract_field(ai_response, "graph_instructions")
                state.is_graph_needed = extract_field(ai_response, "is_graph_needed")
                break
            except Exception as e:
                print("Error in main_agent_call:", e)
                cnt+=1
                error = str(e)[:500]
                error_notes += "\n\n"+error
                state.output_text= "Error in main_agent_call"
        return state
 
class GraphAgent:
    def __init__(self,model:BaseChatModel) -> None:
        self.model =  model.with_structured_output(GraphResponse)

        self.prompt_template = self._get_prompt_template()
    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    """You are a weather visualizer.
        You generate Python code using Plotly (and optionally pandas) to visualize weather data.
        Your code must produce a figure stored in a variable named `fig`.
        """,
                ),
                (
                    "user",
                    """ Visualize the weather data using the following instructions:

        {instructions}

        Constraints:
        - You may use pandas *only for data transformation* if necessary.
        - The final visualization must use only Plotly (px or go (already imported)).
        - Store the final plot in a variable called `fig`.
        - The `fig` must be JSON-serializable using `pio.to_json(fig)`.
        - Do not include file saving or display (`.show()`) in your output.
        - Output only Python code — no explanations or markdown.
            """,
                ),
            ]
        )
        return prompt_template
    def invoke(self, state:AgentState):
        """the graph generation agent which produces the graph based on the instructions provided

        Args:
            state (AgentState): the state of the graph
        """
        instructions = state.graph_instructions
        error_notes = ""

        for i in range(state.retry_count+1):
            try:
                full_instructions = instructions
                if error_notes:
                    full_instructions += f"\nNote: the last attempt failed with this error:\n{error_notes}"
                
                prompt = self.prompt_template.invoke(instructions=full_instructions)
                output = self.model.invoke(prompt)
                graph = exec_and_validate(output.graph_code)
                state.graph_json = graph
                break
            except Exception as e:
                error_notes = str(e)[:500]  
                state.graph_json ="""{"error": "error in generating graph"}"""
                print("Error in generating graph:", e)
                print("Retrying...")
        return state

class AgentExecuter:
    def __init__(self, main_agent:MainAgent, graph_agent:GraphAgent) -> None:
        self.main_agent = main_agent
        self.graph_agent = graph_agent
    def invoke(self, state:AgentState):
        
        state = self.main_agent.invoke(state)
        if state.is_graph_needed:
            state = self.graph_agent.invoke(state)
        return state
def main():
    main_agent = MainAgent(model=model,tools=tools,memory=memory,thread_id="thread123")
    graph_agent = GraphAgent(model)

    app = AgentExecuter(main_agent=main_agent,graph_agent=graph_agent)

    while True:
        user_input = input("user(exit to exit):")
        print("\n")
        if user_input == "exit":
            break
        state = AgentState(
            user_query=user_input,
            output_text="",
            graph_instructions="",
            is_graph_needed=False,
            graph_json="",
            retry_count=3,
        )
        result = app.invoke(state)
        print("agent:",result.output_text)
    
        if result.is_graph_needed:
            fig_json = result.graph_json
            fig = pio.from_json(fig_json)
            fig.show()
            print(result.graph_json)

        print("\n")

if __name__ == "__main__":
    main()