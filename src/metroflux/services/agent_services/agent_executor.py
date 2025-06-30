from langchain.tools import Tool

from datetime import date
from typing import List
import json


from metroflux.services.agent_services.agent_schemas import (
    RouterResponse
    , DateResponse
    , SummarizerResponse
    , FinalResponse

)
from metroflux.services.agent_services.main_agent import SummarizerAgent, DateAgent, RouterAgent
from metroflux.services.agent_services.location_service import LocationService
from metroflux.services.agent_services.graph_agent import GraphAgent


class AgentExecuter:
    def __init__(self, SummarizerAgent: SummarizerAgent, DateAgent: DateAgent, RouterAgent: RouterAgent, graph_agent: GraphAgent,location_service:LocationService,tools_list:List[Tool]) -> None:
        self.summarizer_agent = SummarizerAgent
        self.date_agent = DateAgent
        self.router_agent = RouterAgent
        self.graph_agent = graph_agent
        self.location_service = location_service
        self.tools_list = tools_list
        self.tool_map = {tool.name: tool.func for tool in tools_list}
    def invoke(self, user_query:str)->FinalResponse:
        """it will invoke the chain of agents

        Args:
            user_query (str): user query to be processed by the agents
        """
        router_response:RouterResponse = self.router_agent.invoke(user_query=user_query,tools=self.tools_list)

        if router_response.location_based:
            location = self.location_service.get_coordinates_from_location(router_response.location)
            if location is None:
                raise Exception("Location resolution failed.")
            lat, lon = location
        else:
            lat = lon = None


        if router_response.route == "general":
            summarizer_response:SummarizerResponse = self.summarizer_agent.invoke(user_query=user_query,data="none")
            return FinalResponse(summary=summarizer_response.summary,is_graph_needed=summarizer_response.is_graph_needed,graph_json='')
        if router_response.route =="weather_current":
            tool_func = self.tool_map[router_response.route]
            data = tool_func(user_query, lat, lon)
        else:
            today = date.today()
            date_response:DateResponse = self.date_agent.invoke(user_query=user_query,current_date =today)
            tool_func = self.tool_map["weather_summary"]
            data = tool_func(lat, lon, date_response.start_date, date_response.end_date)
        data_json = json.dumps(data)
        summarizer_response:SummarizerResponse = self.summarizer_agent.invoke(user_query=user_query,data=data_json) 
        graph_json =  ""
        if(summarizer_response.is_graph_needed):
            graph_response = self.graph_agent.invoke(summarizer_response.graph_instructions)
            graph_json = graph_response
        final_response = FinalResponse(summary=summarizer_response.summary,is_graph_needed=summarizer_response.is_graph_needed,graph_json=graph_json)
        return final_response