from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models.base import BaseChatModel
from metroflux.services.agent_services.agent_schemas import GraphResponse
from metroflux.services.code_executor import CodeExecutor
from metroflux.services.agent_services.agent_schemas import AgentState
class GraphAgent:
    def __init__(self, model: BaseChatModel) -> None:
        self.model = model.with_structured_output(GraphResponse)

        self.prompt_template = self._get_prompt_template()
        self.code_executor = CodeExecutor()
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

    def exec_and_validate(self, code):
        try:
            if "fig" not in code:
                raise Exception("fig not found in code")
            local_vars = self.code_executor.exec_code(code)
            if "fig" not in local_vars:
                raise Exception("fig not found in code")
            fig = local_vars["fig"]
            fig_json = fig.to_json()
            return fig_json
        except Exception as e:
            print("Error in validating code:", e)
            raise e

    def invoke(self, state: AgentState):
        """the graph generation agent which produces the graph based on the instructions provided

        Args:
            state (AgentState): the state of the graph
        """
        instructions = state.graph_instructions
        error_notes = ""

        for i in range(state.retry_count + 1):
            try:
                full_instructions = instructions
                if error_notes:
                    full_instructions += f"\nNote: the last attempt failed with this error:\n{error_notes}"

                prompt = self.prompt_template.format(instructions=full_instructions)
                output = self.model.invoke(prompt)
                graph = self.exec_and_validate(output.graph_code)
                state.graph_json = graph
                break
            except Exception as e:
                error_notes = str(e)[:500]
                state.graph_json = """{"error": "error in generating graph"}"""
                print("Error in generating graph:", e)
                print("Retrying...")
        return state

