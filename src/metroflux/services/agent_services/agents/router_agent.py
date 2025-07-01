from typing import List

from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder

from metroflux.services.agent_services.agent_schemas import (
    RouterResponse,
)



class RouterAgent:
    def __init__(
        self,
        model: BaseChatModel,
    ):
        self.model = model.with_structured_output(RouterResponse)
        
        self.prompt_template = self._get_prompt_template()
        self.history = []

    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                ("system", "You are a weather assistant router agent .\n"
                 "-use also the context provided by previous chats in history"),
                  MessagesPlaceholder(variable_name="history"),

                (
                    "user",
                    """User query: {user_query}

                    Available routing options:
                    {tool_descriptions}

                    Decide the best route:
                    - Choose the appropriate tool based on the query.
                    - If it's nmot weather-related, route to "general".
                    If user doesn't specify a location but did in previous chats, use that location.

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

        prompt_messages = self.prompt_template.format_messages(
            user_query=user_query,
            tool_descriptions=tool_descriptions,
                history=self.history

        )


        output = self.model.invoke(prompt_messages)
        self.history.append(HumanMessage(content=user_query))
        self.history.append(AIMessage(content=output.model_dump_json()))
        print("Router Response:\n", output, "\n\n")
        return output
