from langchain.chat_models import init_chat_model
from metroflux.services.agent_services.tools import tool_list
from metroflux.services.agent_services.agent_executor import AgentExecuter
from metroflux.services.agent_services.agents import DateAgent, RouterAgent, SummarizerAgent,GraphAgent
from metroflux.services.location_service import LocationService


class AgentExecuterFactory:

    def create_agent_executer(self,thread_id,model_name:str,model_provider:str) -> AgentExecuter:
        model = init_chat_model(model=model_name, model_provider=model_provider)
        summarize_agent = SummarizerAgent(model=model)
        date_agent = DateAgent(model=model)
        router_agent = RouterAgent(model=model)

        graph_agent = GraphAgent(model=model)
        return AgentExecuter(SummarizerAgent=summarize_agent, DateAgent=date_agent, RouterAgent=router_agent, graph_agent=graph_agent,location_service=LocationService(),tools_list=tool_list)
    