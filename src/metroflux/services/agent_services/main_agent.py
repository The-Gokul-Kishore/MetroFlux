from typing import List

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from metroflux.services.agent_services.agent_schemas import (
    AgentState,
    RouterResponse,
    SummarizerResponse,
    DateResponse
)
from metroflux.services.json_extractor import JsonExtractor


def pre_model_hook(self, state):
    trimmed = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=2048,
        start_on="human",
        end_on=("human", "tool"),
        include_system=True,
    )
    return {"llm_input_messages": trimmed}


class RouterAgent:
    def __init__(
        self,
        model: BaseChatModel,
    ):
        self.model = model.with_structured_output(RouterResponse)
        self.prompt_template = self._get_prompt_template()

    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                ("system", "You are a weather assistant router agent .\n"),
                (
                    "user",
                    """User query: {user_query}

                    Available routing options:
                    {tool_descriptions}

                    Decide the best route:
                    - Choose the appropriate tool based on the query.
                    - If it's not weather-related, route to "general".
                    - Set `location_based` to True if the query requires geographic location (like a city name), else False.
                    """,
                ),
            ]
        )
        return prompt_template

    def invoke(self, user_query:str,tools:List[Tool]) -> RouterResponse:
        print("router invoked")
        tool_descriptions = "\n".join(
            [f"- {tool.name}: {tool.description}" for tool in tools]
        )

        prompt = self.prompt_template.invoke(
            {"user_query": user_query, "tool_descriptions": tool_descriptions}
        )
        output = self.model.invoke(prompt)
        print("Router Response:\n", output, "\n\n")
        return output
class DateAgent:
    def __init__(
        self,
        model: BaseChatModel,
    ):
        self.model = model.with_structured_output(DateResponse)
    
        self.prompt_template = self._get_prompt_template()
    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    """you are a weather assistant's date resolver give correct date ranges for the query"""
                    ),
                (
                    "user",
                    """User query: {user_query}
                        current_date is {current_date}
                        based on the current date and user query return date ranges

                    """
                )
                                        
            ]
        )
        return prompt_template
    def invoke(self, user_query:str,current_date:str) -> DateResponse:
        print("date resolver invoked")
        prompt = self.prompt_template.invoke(
            {"user_query": user_query, "current_date": current_date}
        )
        output = self.model.invoke(prompt)
        print("Date Response:\n", output, "\n\n")
        return output


class SummarizerAgent:
    def __init__(
        self,
        model: BaseChatModel,
    ):
        self.model = model.with_structured_output(SummarizerResponse)
        self.propmt_template = self._get_prompt_template()

    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are a weather assistant summarizer agent use data to address user query and also graph if needed.\n"
                    "- Use the provided weather data to answer the user's query.\n",
                ),
                (
                    "user",
                    """User query: {user_query}

                    Given the following weather data:

                    {data}

                    Do the following:
                    1. Summarize the weather data to address the user's query.
                    2. Set `is_graph_needed` to true if the query involves trends, forecasts, or time series data.
                    3. If a graph is needed, include `graph_instructions` using this format:
                    "Line chart with date on x-axis, temperature (°C) on y-axis. Data: [...]. Use blue color for the line."
                    """,
                ),
            ]
        )
        return prompt_template

    def invoke(self, user_query: str, data: str) -> SummarizerResponse:
        print("summarizer invoked")
        prompt = self.propmt_template.invoke(
            {"user_query": user_query, "data":data}
        )
        output = self.model.invoke(prompt)
        print("Summarizer Response:\n", output, "\n\n")
        return output


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
            model=model,
            pre_model_hook=pre_model_hook,
            checkpointer=memory,
            tools=tools,
        )
        self.config = {"configurable": {"thread_id": thread_id}}
        self.json_extractor = json_extractor
        self.prompt_template = self._get_prompt_template()

    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are a weather assistant.\n"
                    "- Never guess or answer directly.\n"
                    "- Always use tools to get data.\n"
                    "- Always reply in this exact JSON format:\n"
                    "```json\n"
                    "{{\n"
                    '  "output_text": "...",\n'
                    '  "is_graph_needed": true or false,\n'
                    '  "graph_instructions": "..." \n'
                    "}}\n"
                    "```\n"
                    "If the user asks non-weather questions, politely redirect them to weather queries.",
                ),
                (
                    "user",
                    "User query: {user_query}\n\n"
                    "Follow these steps:\n"
                    "1. Use TavilySearch to get coordinates.\n"
                    "2.Only ONE tool should be called per query, based on intent. Pick one tool: weather_current, weather_future, weather_past, or weather_summary.\n"
                    "3. Output valid JSON only (no text outside the block).\n\n"
                    "Graph is needed if trends or date ranges are asked.(lean towards prodcuing graph for forecasts)\n"
                    "Example 1 (no graph):\n"
                    "```json\n"
                    "{{\n"
                    '  "output_text": "It is 27°C in Delhi with clear skies.",\n'
                    '  "is_graph_needed": false,\n'
                    '  "graph_instructions": ""\n'
                    "}}\n"
                    "```\n\n"
                    "Example 2 (with graph):\n"
                    "```json\n"
                    "{{\n"
                    '  "output_text": "Here is the 5-day forecast.",\n'
                    '  "is_graph_needed": true,\n'
                    '  "graph_instructions": "Line chart with date on x-axis, temperature (°C) on y-axis. Data: [...]"\n'
                    "}}\n"
                    "```",
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
                print("Agent Messages:\n", output["messages"], "\n\n")

                raw_ai_response = next(
                    (
                        msg.content
                        for msg in reversed(output["messages"])
                        if msg.type == "ai"
                    ),
                    "",
                )
                print("Raw AI Response:\n", raw_ai_response, "\n\n")
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
