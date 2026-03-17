from typing import Dict
from langgraph.graph import StateGraph, START, END
from src.data_models.schemas import BuildState
from langchain_core.messages import  HumanMessage, AIMessage
from src.agents.game_dev_agent.nodes import plan_node,project_tools_node,build_tool_node,fixer_node,apply_fix_actions_node, enhancement_node, error_analyzer, code_retriever, summarizer


class GraphBuilder():

    def _start_router(self, state: BuildState)-> str:
        if state.get("n_rounds") > 0 :
            return "retriever"
        else:
            return "summarizer"
        
    def _route_after_tools(self, state: BuildState) -> str:
        return "build" if state.get("execution_success") else "end"

    def _route_after_build(self, state: BuildState) -> str:
        if state.get("build_ok"):
            return "end"

        if (state.get("fix_attempts")) >= 7:
            return "end"
        return "error_analyzer"
    
    def _route_after_analyzer(self, state: BuildState):
        if state.get("is_error"):
            return "fixer"
        else:
            return "end"
    def _route_after_apply(self, state: BuildState) -> str:
        return "build"
    
    def init_state(self, requirements : str):
        return {
            "n_rounds": 0,
            "requirements": requirements,
            "summary" : "",
            "game_name" : "" ,
            "description": "",
            "development_plan": "",
            "directories": [],
            "files": [],
            "packages": [],
            "messages": [],
            "last_tool_result": None,
            "execution_success": None,
            "build_ok": None,
            "build_output": "",
            "is_error" : None , 
            "error_files" : [],
            "root_cause" : "",
            "fix_plan": {},
            "fix_actions_result": [],
            "fix_attempts": 0,
            "retrieved_files" : []

        }

    def build_app(self, checkpointer=None):
        graph = StateGraph(BuildState)
        graph.add_node("summarizer" , summarizer)
        graph.add_node("retriever",code_retriever)
        graph.add_node("enhancer" , enhancement_node)
        graph.add_node("plan", plan_node)          
        graph.add_node("tools", project_tools_node)  
        graph.add_node("build", build_tool_node)  
        graph.add_node('error_analyzer', error_analyzer) 
        graph.add_node("fixer", fixer_node)   
        graph.add_node('apply_fixes',apply_fix_actions_node)

        
        graph.add_conditional_edges(
            START,
            self._start_router,
            {"retriever": "retriever", "summarizer": "summarizer"},
        )
        graph.add_edge("summarizer","plan")
        graph.add_edge("retriever", "enhancer")
        graph.add_edge('plan','tools' )
        graph.add_conditional_edges(
            "tools",
            self._route_after_tools,
            {"build": "build", "end": END},
        )
        graph.add_conditional_edges(
            "build",
            self._route_after_build,
            {"error_analyzer": "error_analyzer", "end": END},
        )

        graph.add_conditional_edges(
            "error_analyzer",
            self._route_after_analyzer,
            {"fixer" :"fixer",  "end": END}
        )
        graph.add_edge("fixer", 'apply_fixes')

        graph.add_conditional_edges(
            "apply_fixes",
            self._route_after_apply,
            {"build": "build"},
        )

        return graph.compile(checkpointer=checkpointer)
