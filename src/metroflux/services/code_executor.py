import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

class CodeExecutor:
    def exec_code(self,code):
        try:
            local_vars = {}
            exec(code, {"pd": pd, "px": px, "go": go, "pio": pio}, local_vars)
            return local_vars
        except Exception as e:
            print("Error in executing code:", e)
            raise e

