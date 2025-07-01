from langchain.prompts import ChatPromptTemplate
from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder


from metroflux.services.agent_services.agent_schemas import SummarizerResponse


class SummarizerAgent:
    def __init__(
        self,
        model: BaseChatModel,
    ):
        self.model = model.with_structured_output(SummarizerResponse)
        self.propmt_template = self._get_prompt_template()
        self.history = []

    def _get_prompt_template(self):
        prompt_template = ChatPromptTemplate(
            [
                (
                    "system",
                    "You are a weather assistant summarizer agent use data to address user query and also graph if needed.\n"
                    "- Use the provided weather data to answer the user's query.\n"
                    "- If the current query lacks some context (e.g., location, type of weather), try to infer it from the previous chat history."
                    "- If no weather data is available, respond politely with a general message and encourage the user to ask a weather-related question."
                    "- if no weather data provided and query is general answer in polite tone while also pushing user to ask weather related question and ask use for weather question",
                ),
                MessagesPlaceholder(variable_name="history"),
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
        prompt = self.propmt_template.format_messages(
            user_query=user_query, data=data, history=self.history
        )
        output = self.model.invoke(prompt)
        self.history.append(HumanMessage(content=user_query))
        self.history.append(AIMessage(content=output.model_dump_json()))
        print("Summarizer Response:\n", output, "\n\n")
        return output
