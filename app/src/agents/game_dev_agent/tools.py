import os
from pathlib import Path
from typing import List, Dict
from langchain.tools import tool
from src.utils.command_utils import CommandUtils
from src.agents.game_dev_agent.tool_helpers import execute_plan
from src.data_models.schemas import ProjectPlan
from configs import WORKSPACE_DIR, MIN_NODE, PACKAGE_MANAGER



 
command_utils = CommandUtils(workspace=WORKSPACE_DIR, min_node=MIN_NODE, package_manager=PACKAGE_MANAGER)

@tool("execute_project_plan")
def execute_project_plan_tool(plan: Dict) -> Dict:
    """
    Execute a project plan (dict). 
    Returns: {"success": bool, "error"?: str}
    """
    try:
        ok = execute_plan(ProjectPlan(**plan))
        return {"success": bool(ok)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool("write_file")
def write_file_tool(path: str, content: str) -> Dict:
    """Create/overwrite a file with content (relative to workspace)."""
    try:
        command_utils.create_file(path, content or "")
        return {"ok": True, "path": path}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": path}

@tool("read_file")
def read_file_tool(path: str) -> Dict:
    """Read a file content (relative to workspace)."""
    try:
        data = command_utils.read_file(path)  
        return {"ok": True, "path": path, "content": data}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": path}

@tool("install_package")
def install_package_tool(name: str, dev: bool = False) -> Dict:
    """Install an npm package."""
    try:
        command_utils.install_package(name, dev)
        return {"ok": True, "name": name, "dev": dev}
    except Exception as e:
        return {"ok": False, "error": str(e), "name": name, "dev": dev}   
    
@tool("run_script")
def run_script_tool(script: str) -> Dict:
    """Run an npm script, e.g., 'build' or 'dev'."""
    try:  
        out, err = command_utils.run_script(script)  
        if len(err) > 0 :
            return  {"ok": False, "message": err, "script": script}
        else :
            print("------------------"*5)
            print(f"it is a build error : {err} ")
            print("------------------"*5)
            return  {"ok": True, "message": out, "script": script}

    except Exception as e:
       print(f"Build failed because of python Error : {e}")
       raise


TOOL_REGISTRY = {
    "run_script": run_script_tool,
}

def get_tools_by_names(tool_names: List[str]):
    return [TOOL_REGISTRY[name] for name in tool_names]