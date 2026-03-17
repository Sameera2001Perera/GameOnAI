
from pydantic import BaseModel, Field
from typing import List, TypedDict, Annotated, Dict, Optional, Any, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import  BaseMessage

import json
from pydantic import BaseModel, Field, field_validator

class PackageInfo(BaseModel):
    name: str = Field(description="Package name")
    dev: bool = Field(default=False, description="Whether it's a dev dependency")

class FileInfo(BaseModel):
    path: str = Field(description="File path relative to project root")
    description: str = Field(description="What this file does")
    content: str = Field(description="code content")

class ProjectPlan(BaseModel):
    description: str = Field(description="Brief project description")
    development_plan: str = Field(description="full game development")
    directories: list[str] = Field(description="List of directories to create")
    files: list[FileInfo] = Field(description="List of files to create with content")
    packages: list[PackageInfo] = Field(default=[], description="List of packages to install")



class FixAction(BaseModel):
    tool: Literal["write_file", "install_package","remove_file"]
    args: Dict[str, Any] = Field(default_factory=dict)

class FixPlan(BaseModel):
    summary: str
    actions: List[FixAction] = Field(default_factory=list)

class ErrorFiles(BaseModel):
    is_error : bool = Field(description="is_any error or not")
    root_cause : str = Field(default = "", description="root cause for the error" )
    files : list[str] = Field(default = [], description="files supposed to be fixed")

class CodeChunks(BaseModel) :
    file_name : str = Field(description="retrieved file name")
    score : float = Field(description="similarity score")
    content : str = Field(description="File Content")

class ChangedContent(BaseModel) :
    file_path : str
    content : str

class UpdatedCode(BaseModel) :
    changes :  List[ChangedContent] 
    description : str

class Summarize(BaseModel):
    summarized_text : str
    game_name : str

class BuildState(TypedDict):
    
    n_rounds : str
    requirements: str
    summary : str
    game_name : str
    description: str
    development_plan: str
    directories: List[str]
    files: List[dict]     
    packages: List[dict]

    messages: Annotated[List[BaseMessage], add_messages]
    last_tool_result: Optional[Dict[str, Any]]
    execution_success: Optional[bool]

    build_ok: Optional[bool]
    build_output: Optional[str]
    is_error : [Optional[bool]]
    error_files : Optional[List[str]]
    root_cause : Optional[str]
    fix_plan: Optional[Dict[str, Any]]
    fix_actions_result: Optional[List[Dict[str, Any]]]
    fix_attempts: Optional[int]

    retrieved_files : Optional[List[CodeChunks]]




