from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models.base import BaseChatModel
from metroflux.services.agent_services.agent_schemas import GraphResponse
from metroflux.services.code_executor import CodeExecutor

class GraphAgent:
    def __init__(self, model: BaseChatModel) -> None:
        self.model = model.with_structured_output(GraphResponse)

        self.prompt_template = self._get_prompt_template()
        self.code_executor = CodeExecutor()
    def _get_prompt_template(self):

        prompt_template = ChatPromptTemplate.from_messages([
            (
                "system",
                """You are a Python code generator for weather visualizations.

        Your job is to:
        - Generate valid Python code using Plotly (and optionally pandas) to visualize the data.
        - Always assign the final plot to a variable named `fig`.

        Constraints:
        - The final output must be **pure Python code**, not JSON or explanations.
        - The variable `fig` must be defined, as it will be serialized using `plotly.io.to_json(fig)`.
        - Do not include `.show()`, `print()`, or any text output — just the code.
        - Do NOT output raw JSON. Always generate Python code using `plotly.graph_objects` or `plotly.express`.

        Only output valid Python code. No markdown, comments, or text outside code."""
            ),
            (
                "user",
                """Visualize the weather data using the following instructions:

        {instructions}

        Make sure:
        - You create a variable named `fig` with the final Plotly graph object.
        - Use only Plotly.
        - Return only valid Python code."""
            )
        ])

        return prompt_template

    def exec_and_validate(self, code):
        try:
            if code.startswith('"""') and code.endswith('"""'):
                code = code[3:-3].strip()

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

    def invoke(self,instructions: str,retry_cnt:int=3)->str:
        """the graph generation agent which produces the graph based on the instructions provided

        Args:
            instructions (str): instructions to generate the graph
            retry_cnt (int, optional): number of retries. Defaults to 3.

        Returns:
            str:plotly graph json
        """
        instructions = instructions
        error_notes = ""
        print("graph agent invoked with :\n", instructions, "\n\n")
        for i in range( retry_cnt+ 1):
            try:
                
                full_instructions = instructions
                if error_notes:
                    full_instructions += f"\nNote: the last attempt failed with this error:\n{error_notes}"

                prompt = self.prompt_template.format(instructions=full_instructions)
                output = self.model.invoke(prompt)
                print("Graph Code:\n", output.graph_code, "\n\n")
                graph = self.exec_and_validate(output.graph_code)
                graph_json = graph
                break
            except Exception as e:
                error_notes = str(e)[:500]
                graph_json = """{"error": "error in generating graph"}"""
                print("Error in generating graph:", e)
                print("Retrying...")
        return graph_json

