from langgraph.prebuilt import create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models.base import BaseChatModel

from typing import List

from metroflux.services.agent_services.agent_schemas import AgentState
from metroflux.services.json_extractor import JsonExtractor
class MainAgent:
    def __init__(
        self,
        model: BaseChatModel,
        tools: List[Tool],
        memory: MemorySaver,
        thread_id: str,
        json_extractor: JsonExtractor,
    ):
        self.executor = create_react_agent(
            model=model, checkpointer=memory, tools=tools
        )
        self.config = {"configurable": {"thread_id": thread_id}}
        self.json_extractor = json_extractor
        self.prompt_template = self._get_prompt_template()

    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are a helpful weather assistant. Always use tools to answer  weather related queries. "
                    "if the user query is not related to weather, answer with following same json format (while answering trivial questions like 'hi') and push user to ask about weather'."
                    "Never guess or invent data.",
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
        """,
                ),
            ]
        )
        return prompt_template

    def invoke(self, state: AgentState) -> AgentState:
        query = state.user_query
        error_notes = "\n\n errors from previous attempts:"

        print("executing main_agent_call")
        for cnt in range(state.retry_count + 1):
            try:
                prompt = self.prompt_template.invoke(
                    {"user_query": query + error_notes}
                )

                output = self.executor.invoke(prompt, config=self.config)
                raw_ai_response = next(
                    (
                        msg.content
                        for msg in reversed(output["messages"])
                        if msg.type == "ai"
                    ),
                    "",
                )
                ai_response = self.json_extractor.extract_json(raw_ai_response)
                state.output_text = self.json_extractor.extract_field(
                    ai_response, "output_text"
                )
                state.graph_instructions = self.json_extractor.extract_field(
                    ai_response, "graph_instructions"
                )
                state.is_graph_needed = self.json_extractor.extract_field(
                    ai_response, "is_graph_needed"
                )
                break
            except Exception as e:
                print("Error in main_agent_call:", e)
                error = str(e)[:500]
                error_notes += "\n\n" + error
                state.output_text = "Error in main_agent_call"
        return state

