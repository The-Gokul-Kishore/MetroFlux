from langchain.prompts import ChatPromptTemplate
from langchain.chat_models.base import BaseChatModel

from metroflux.services.agent_services.agent_schemas import SummarizerResponse


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
                    "- Use the provided weather data to answer the user's query.\n"
                    "- if no weather data provided and query is general answer in polite tone while also pushing user to ask weather related question",
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
        prompt = self.propmt_template.invoke({"user_query": user_query, "data": data})
        output = self.model.invoke(prompt)
        print("Summarizer Response:\n", output, "\n\n")
        return output
