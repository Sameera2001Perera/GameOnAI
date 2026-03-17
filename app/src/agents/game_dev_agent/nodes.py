import os
import re
import json
import shutil
from pathlib import Path
from typing import List, TypedDict, Annotated, Dict, Optional, Any
from langchain_anthropic import ChatAnthropic
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, ToolMessage, BaseMessage, HumanMessage
from langchain_core.messages import ToolMessage
from langchain.tools import tool

from configs import ANTHROPIC_API_KEY
from src.data_models.schemas import ProjectPlan, FixPlan, BuildState, Summarize
from src.agents.game_dev_agent.tools import read_file_tool, execute_project_plan_tool
from src.utils.command_utils import CommandUtils
from src.agents.game_dev_agent.tool_helpers import execute_plan
from src.data_models.schemas import ProjectPlan, ErrorFiles, UpdatedCode
from configs import WORKSPACE_DIR, TEMPLATE_DIR, MIN_NODE, PACKAGE_MANAGER, prompt_template, sample_prompt, fixer_prompt, improver_prompt, INSTRUCTIONS, summarizer_prompt
from prompt_store import PromptStore
from src.agents.game_dev_agent.codeEmbedding import CodeEmbeddings

MONGO_URI = "mongodb+srv://lahiruprabhath099:qYVDTCA22Mds96KV@cluster1.diq5rte.mongodb.net/?retryWrites=true&w=majority&appName=Cluster1&tlsAllowInvalidCertificates=true"
store = PromptStore(MONGO_URI, db_name="GameOnAI", collection_name="prompts")


print(f"workspace_inside_nodes : {WORKSPACE_DIR}")
 
command_utils = CommandUtils(workspace=WORKSPACE_DIR, min_node=MIN_NODE, package_manager=PACKAGE_MANAGER)


@tool("execute_project_plan")
def execute_project_plan_tool(plan: Dict) -> Dict:
    """
    Execute a project plan (dict). 
    Returns: {"success": bool, "error"?: str}
    """
    try:
        print(f"executing_tool : {plan}")
        ok = execute_plan(ProjectPlan(**plan))
        return {"success": bool(ok)}
    except Exception as e:
        return {"success": False, "error": str(e)}
    
@tool("write_file")
def write_file_tool(path: str, content: str) -> Dict:
    """Create/overwrite a file with content (relative to workspace)."""
    try:
        command_utils.create_file(path, content = "")
        return {"ok": True, "path": path}
    except Exception as e:
        return {"ok": False, "error": str(e), "path": path}

@tool("read_file")
def read_file_tool(path: str) -> Dict:
    """Read a file content (relative to workspace)."""
    try:
        data = command_utils.read_file(path)  # ensure you have this helper
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
        print("--------------------"*10) 
        print(f"out : {out} , \nerr: {err}")
        print("--------------------"*10) 
        if len(err) > 0 :
            return  {"ok": False, "message": err, "script": script}
        else :
            return  {"ok": True, "message": out, "script": script}

    except Exception as e:
       print(f"Build failed because of python Error : {e}")
       raise

def summarizer(state : BuildState):

    print("Graph running started" )
    llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.1, api_key=ANTHROPIC_API_KEY, max_tokens_to_sample=32000)
    structured_llm = llm.with_structured_output(Summarize)
    formatted_prompt = summarizer_prompt.format(user_query = state.get("requirements"))
    response : Summarize = structured_llm.invoke([HumanMessage(content=formatted_prompt)]) 
    response = response.model_dump()
    print(response)
    return {
        "game_name" : response["game_name"],
        "summary" : response["summarized_text"]
    }
def get_project_plan(requirements: str):
    """Get a project plan from LLM."""
    print("🤖 Getting project plan from LLM...")
    try:
        sub_comm_utils = CommandUtils(workspace=Path(os.path.join(os.getcwd(), "templates/workspace")), min_node=MIN_NODE, package_manager=PACKAGE_MANAGER)

        if os.path.exists(os.path.join(os.getcwd(), 'workspace')):
            shutil.rmtree(os.path.join(os.getcwd(), 'workspace'))

            print("Removing workspace !")

        main_page = sub_comm_utils.read_file('app/page.tsx')
        command_utils.move_file(TEMPLATE_DIR, os.path.join(os.getcwd() , 'workspace'))

        command_utils.remove_file(path = "app/page.tsx")

        llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0.1, api_key=ANTHROPIC_API_KEY, max_tokens_to_sample=32000)
        structured_llm = llm.with_structured_output(ProjectPlan)

        formatted_prompt = sample_prompt.format(requirements=requirements, main_page=main_page)
        response  = llm.invoke([HumanMessage(content=formatted_prompt)])   
        raw = response.content  # from llm.invoke(...)
        parsed_json = extract_json_object(raw)
        response = ProjectPlan(**parsed_json)
        print(f"plan : {response}")
        return response           
    except Exception as e:
        print(f"❌ Error getting project plan: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
def extract_json_object(text: str) -> dict:
    if not text or not text.strip():
        raise ValueError("Empty LLM response; no JSON to parse")

    s = text.strip()

    # Strip ```json ... ``` or ``` ... ```
    if s.startswith("```"):
        s = re.sub(r"^```(?:json)?\s*|\s*```$", "", s, flags=re.DOTALL).strip()

    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM response")

    candidate = s[start:end+1]
    return json.loads(candidate)   

def plan_node(state: BuildState):
    """Call LLM once, fill state with the plan, and enqueue a tool call."""
    print(f"round {state["n_rounds"]}")
    plan_obj = get_project_plan(state["summary"])
    
    if plan_obj is None:
        
        return {"messages": [AIMessage(content="Failed to get plan; skipping tool call.")],
        }
    plan = plan_obj.model_dump()
    
    return {
        "description": plan["description"],
        "development_plan": plan["development_plan"],
        "directories": plan["directories"],
        "files": plan["files"],
        "packages": plan["packages"],
        "messages": [
            AIMessage(
                content="Executing generated project plan.",
                tool_calls=[{
                    "name": "execute_project_plan",
                    "args": {"plan" : plan},
                    "id": "call-0",
                }],
            )
        ],
    }


def project_tools_node(state: BuildState):
    _scaffold_tool_node = ToolNode([execute_project_plan_tool])
    out = _scaffold_tool_node.invoke({"messages": state["messages"]})
    msgs: List[BaseMessage] = out["messages"] if isinstance(out, dict) else out

    tool_msg = next((m for m in reversed(msgs) if isinstance(m, ToolMessage)), None)
    print(f"project tool message: {tool_msg}")
    if not tool_msg:
        result: Dict[str, Any] = {"success": False, "error": "No ToolMessage returned"}
    else:
        payload = tool_msg.content
        if isinstance(payload, dict):
            result = payload
        else:
            try:
                result = json.loads(payload)
            except Exception:
                result = {"success": False, "error": f"Non-JSON tool output: {payload}"}

    updates: Dict[str, Any] = {
        "messages": [
            AIMessage(
                content="Building the project.",
                tool_calls=[{
                    "name": "run_script",
                    "args": {"script" : "build"},
                    "id": "call-1",
                }],
            )
        ], 
        "last_tool_result": result,
        "execution_success": bool(result.get("success")),
    }
    if result.get("success"):
        files_list = state.get("files", [])
        updates["file_states"] = {f["path"]: {"written": False} for f in files_list}

    return updates

def build_tool_node(state: BuildState):
    print(f"🏗️ Running build for the {state.get("fix_attempts")+1} time...")
    build_tool = ToolNode([run_script_tool])

    out = build_tool.invoke({"messages": state.get("messages", [])})
    msgs: List[BaseMessage] = out["messages"] if isinstance(out, dict) else out

    
    tool_msg = next((m for m in reversed(msgs) if isinstance(m, ToolMessage)), None)
    print(f"build tool message: {tool_msg}")
    if not tool_msg:
        result: Dict[str, Any] = {"ok": False, "message": "No ToolMessage returned from build."}
    else:
        payload = tool_msg.content
        if isinstance(payload, dict):
            result = payload
        else:
            try:
                result = json.loads(payload)
            except Exception:
                result = {"ok": False, "message": f"Non-JSON tool output: {payload}"}

    return {
        "messages": msgs,
        "last_tool_result": result,
        "build_ok": bool(result.get("ok")),
        "build_output": result.get("message", ""),
    }

def error_analyzer(state: BuildState):

    prompt = store.get_prompt("error_analyzer_prompt") 

    llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.1, api_key=ANTHROPIC_API_KEY, max_tokens_to_sample=8192)
    structured_llm = llm.with_structured_output(ErrorFiles)
    print(f" Build output : {state.get("build_output")}")
    formatted_prompt = prompt.format(error=state.get("build_output"), files = state.get("files"))
    response : ErrorFiles = structured_llm.invoke([HumanMessage(content=formatted_prompt)]) 
    response = response.model_dump()

    if not response["is_error"] :
        state["n_rounds"] += 1
        state["build_ok"] = True
        state["fix_attempts"] = 0

        print(f"Build is completed successfully")
        print(state["messages"])

    return {
        "is_error" : response["is_error"],
        "error_files" : response["files"],
        "root_cause" : response["root_cause"],
        "n_rounds" : state["n_rounds"],
        "fix_attempts" : state["fix_attempts"] 
    
    }

def code_fixer(state: BuildState):
    """
    LLM agent that analyzes the failed npm build output and returns a structured FixPlan (Pydantic).
    It proposes a sequence of tool actions (read_file, write_file, install_package) to fix the error.
    """
    build_log = state.get("build_output") 
    if not build_log.strip():
        return {
            "fix_plan": None,
            "messages": state.get("messages", []) + [AIMessage(content="No build output to diagnose.")],
        }
    prompt_template = store.get_prompt("code_fixer_prompt") 
    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.1,
            api_key=ANTHROPIC_API_KEY,
            max_tokens_to_sample=24000,
        )

        structured_llm = llm.with_structured_output(FixPlan)

        files=state.get("error_files")
        print(f"error files : {files}")
        code_list = []
        for file in files:
            data = read_file_tool(file)
            code_content = file + f"\n{data}"
            code_list.append(code_content)
        errro_codes = "\n\n".join(code_list)


        formatted_prompt = fixer_prompt.format(error=state.get("build_output",""), root_cause = state.get("root_cause"), current_code=errro_codes)
        fixer_response : FixPlan = structured_llm.invoke([HumanMessage(content=formatted_prompt)]) 
        print(f"fixing plan : {fixer_response}")   
        return fixer_response        
    except Exception as e:
        print(f"❌ Error fixing code: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def fixer_node(state : BuildState):
    fixer_response = code_fixer(state)
    if fixer_response is None:     
        return {"messages": [AIMessage(content="Failed to fix the build error; skipping tool call.")],
        }
    fix_plan = fixer_response.model_dump()
    return {
        "fix_plan": fix_plan,
        "messages": state.get("messages", []) + [AIMessage(content="Fix plan generated.")],
        
    }
def apply_fix_actions_node(state: BuildState):
    plan = state.get("fix_plan") or {}
    actions: List[Dict[str, Any]] = plan.get("actions", [])
    print(f'fix plan inside apply : {plan}')
    results: List[Dict[str, Any]] = []
    TOOL_REGISTRY = {
        "write_file": command_utils.create_file,
        "install_package": command_utils.install_package,
        "remove_file" : command_utils.remove_file
    }

    for i, action in enumerate(actions):
        tool_name = action.get("tool")
        args = action.get("args", {})
        func = TOOL_REGISTRY.get(tool_name)
        print(f"selected func : {func} \nargs : {args}")
        if not func:
            results.append({"index": i, "tool": tool_name, "ok": False, "error": "Unknown tool"})
            continue
        try:
            res = func(**args)
        except Exception as e:
            print(f"❌ {func} function failed calling. error : e")
            res = {"ok": False, "error": str(e)}

    print(f'action_appied results : {results}')

    return {
        "fix_actions_result": res,
        "messages": AIMessage(
                content="Fixes applying, re-building the project.",
                tool_calls=[{
                    "name": "run_script",
                    "args": {"script" : "build"},
                    "id": "call-1",
                }],
            ),
        "fix_attempts" : state.get("fix_attempts") + 1
    }


def code_retriever(state: BuildState, score_threshold=0.3):

    embedder = CodeEmbeddings()
    chunk_count = embedder.populate_workspace(WORKSPACE_DIR)
    print(f"Working on changes !")

    retrieved_files = []
    for message in reversed(state["messages"]):

        if isinstance(message, HumanMessage):

            results = embedder.search(query=message.content)
            print(f"files before filter : {results}")

            unique_files = embedder.get_uniques(results)

            for i, result in enumerate(unique_files):
                print(f"files_after_filtered : \n{result}")
                if result["score"] > score_threshold:
                    
                    file = result['file_path']
                    score = result['score']
                    data = command_utils.read_file(file_path=file)

                    chunk = {"file_path" : file,
                            "score" : score,
                            "content" : data
                            }
                    
                    retrieved_files.append(chunk)
            print(f"retrieved_files : {retrieved_files}")
            return {"retrieved_files": retrieved_files}
    
    
    return {"messages" : AIMessage(
                content="No human message found.")
                }
    

def enhancement_node(state: BuildState):
    print("calling enhancement node !")
    for message in reversed(state["messages"]):
        if isinstance(message, HumanMessage):
            change_request = message.content
    if not change_request :
        raise "No human messages found !"
    retrieved_files = state.get("retrieved_files")
    target_codes = " "
    for chunk in retrieved_files:

        code = f'\n\n{chunk["file_path"]}' + f"\n{chunk["content"]}"
        target_codes = target_codes + code

    try:
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0.1,
            api_key=ANTHROPIC_API_KEY,
            max_tokens_to_sample=24000,
        )

        structured_llm = llm.with_structured_output(UpdatedCode)


        formatted_prompt = improver_prompt.format(instructions=INSTRUCTIONS, requirement = change_request, codes = target_codes)
        changed_response : UpdatedCode = structured_llm.invoke([HumanMessage(content=formatted_prompt)]) 
        response = changed_response.model_dump()
        msg = apply_changes(response)
        print(msg)
        return {
            "messages": AIMessage(
                content=f"re-building the project.",
                tool_calls=[{
                    "name": "run_script",
                    "args": {"script" : "build"},
                    "id": "call-1",
                }],
            ),
        }

    except Exception as e:
        print(f"❌ Error updating code: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    
def apply_changes(response :Dict ):
    try :
        
        print(f"Changes : {response}")
        for change in response["changes"]:
            file_path = change["file_path"]
            content = change["content"]
            command_utils.create_file(path=file_path , content=content)
        return "Successfully updated the codes"
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"❌ Error writing to workspace: {str(e)}"
