from metroflux.services.agent_services.agent_schemas import AgentState
from metroflux.services.agent_services.main_agent import MainAgent
from metroflux.services.agent_services.graph_agent import GraphAgent


class AgentExecuter:
    def __init__(self, main_agent: MainAgent, graph_agent: GraphAgent) -> None:
        self.main_agent = main_agent
        self.graph_agent = graph_agent

    def invoke(self, state: AgentState):
        state = self.main_agent.invoke(state)
        if state.is_graph_needed:
            state = self.graph_agent.invoke(state)
        return state

