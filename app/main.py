from typing import Dict, Any
from flask import Flask, request, jsonify

from langgraph.checkpoint.memory import MemorySaver
from src.agents.game_dev_agent.graph_builder import GraphBuilder
from langchain_core.messages import  HumanMessage
from src.utils.deploy import push_workspace_to_github

app = Flask(__name__)

checkpointer = MemorySaver()
graph_builder = GraphBuilder()
app_graph = graph_builder.build_app(checkpointer=checkpointer)


@app.route("/build", methods=["POST"])
def build_game():
    try:
        payload: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400

    thread_id = payload.get("thread_id")
    requirements = payload.get("requirements")

    if not isinstance(thread_id, str) or not thread_id:
        return jsonify({"ok": False, "error": "`thread_id` (string) is required"}), 400
    if requirements is not None and not isinstance(requirements, str):
        return jsonify({"ok": False, "error": "`requirements` must be a string"}), 400

    config = {"configurable": {"thread_id": thread_id}}

    try:
        snapshot = app_graph.get_state(config)
        has_state = bool(getattr(snapshot, "values", None))
    except Exception:
        has_state = False
        snapshot = None


    if not has_state:
        
        input_state = graph_builder.init_state(requirements=requirements)
    else:

        input_state = {
            "messages": HumanMessage(content=requirements),
        }

 
    for chunk in app_graph.stream(input=input_state, config=config):
        print("---- CHUNK ----")
        print("---------------")

    return jsonify({"Success": True, "message": "Build completed successfully"}), 200


@app.route("/deploy" , methods = ["POST"])
def deploy_to_github():
    try:
        payload: Dict[str, Any] = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "Invalid JSON body"}), 400

    github_repo = payload.get("thread_id")
    branch = payload.get("requirements")
    commit_message = payload.get("commit_message")

    push_workspace_to_github(branch_name=branch , repo_url=github_repo, commit_message=commit_message)

if __name__ == "__main__":  
    app.run(host="0.0.0.0", port=8000, debug=False)
