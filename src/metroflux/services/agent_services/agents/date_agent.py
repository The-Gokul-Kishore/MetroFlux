from langchain.chat_models.base import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from metroflux.services.agent_services.agent_schemas import DateResponse


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
                    """you are a weather assistant's date resolver give correct date ranges for the query""",
                ),
                (
                    "user",
                    """User query: {user_query}
                        current_date is {current_date}
                        based on the current date and user query return date ranges

                    """,
                ),
            ]
        )
        return prompt_template

    def invoke(self, user_query: str, current_date: str) -> DateResponse:
        print("date resolver invoked")
        prompt = self.prompt_template.invoke(
            {"user_query": user_query, "current_date": current_date}
        )
        output = self.model.invoke(prompt)
        print("Date Response:\n", output, "\n\n")
        return output
