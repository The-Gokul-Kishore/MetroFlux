from typing import List

from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool

from metroflux.services.agent_services.agent_schemas import (
    RouterResponse,
    DateResponse
)



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