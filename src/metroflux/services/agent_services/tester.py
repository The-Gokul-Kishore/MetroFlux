from metroflux.services.code_executor import CodeExecutor
code =   """
import plotly.graph_objects as go

fig = go.Figure(data=go.Scatter(x=['2025-06-30', '2025-07-01', '2025-07-02', '2025-07-03', '2025-07-04', '2025-07-05', '2025-07-06', '2025-07-07'], y=[34.8, 34.4, 36.5, 38.1, 38.3, 39.1, 38.1, 38.3], mode='lines', line=dict(color='blue')))
fig.update_layout(title="Temperature (°C) over Time", xaxis_title="Date", yaxis_title="Temperature (°C)")
"""

code_executor = CodeExecutor()
local_vars = code_executor.exec_code(code)
local_vars["fig"].show()