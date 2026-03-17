import threading
from flask import Blueprint, request, jsonify
from src.agents.game_dev_agent import GameDevAgent


chat_bp = Blueprint(
    'chat',           
    __name__,        
    url_prefix='/chat'  
)

game_dev_agent = GameDevAgent()

@chat_bp.route("/build-game", methods=["POST"])
def build_game():
    data = request.get_json()
    print("data received:", data)

    session_id = data.get("session_id", "")
    game_type = data.get("game", "")
    workspace_path = data.get("workspace_path", "")
    if not session_id:
        return jsonify({'error': 'session_id parameter is required'}), 400
    
    # Check if this session exists
    if session_id in game_dev_agent.session_to_env:       
        env_id = game_dev_agent.session_to_env[session_id]
    requirement, message_type = game_dev_agent.handle_input(session_id=session_id,message=game_type)

    thread = threading.Thread(
        target=game_dev_agent.run_in_thread,
        args=(requirement, "", False, 120, workspace_path or None, env_id),
        daemon=True,
    )
    thread.start()

    return jsonify(
        {
            "session_id": session_id,
            "env_id": env_id,
            "message": f"Processing: {game_type}",
            "workspace_path": workspace_path or "./workspace",
            "type": message_type,
        }
    )


