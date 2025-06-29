from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from metroflux.services.agent_services.tools import tool_list
from metroflux.services.agent_services.agent_executor import AgentExecuter
from metroflux.services.agent_services.main_agent import MainAgent
from metroflux.services.agent_services.graph_agent import GraphAgent
from metroflux.services.agent_services.agent_schemas import AgentState
from metroflux.services.json_extractor import JsonExtractor


class AgentExecuterFactory:


    def create_agent_state(self, user_query: str,retry_count: int=3) -> AgentState:
        return AgentState(user_query=user_query, output_text="", graph_instructions="", is_graph_needed=False, graph_json="", retry_count=retry_count)
    
    def create_agent_executer(self,thread_id,model_name:str,model_provider:str) -> AgentExecuter:
        json_extractor = JsonExtractor()
        memory = MemorySaver()
        model = init_chat_model(model=model_name, model_provider=model_provider)
        main_agent = MainAgent(model=model, tools=tool_list, memory=memory, thread_id=thread_id, json_extractor=json_extractor)
        graph_agent = GraphAgent(model=model)
        return AgentExecuter(main_agent=main_agent, graph_agent=graph_agent)