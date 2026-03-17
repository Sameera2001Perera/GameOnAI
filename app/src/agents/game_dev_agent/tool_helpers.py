import os
from langchain.tools import tool
from src.utils.command_utils import CommandUtils
from pathlib import Path
from src.data_models.schemas import ProjectPlan
import json
from configs import WORKSPACE_DIR, MIN_NODE, PACKAGE_MANAGER

command_utils = CommandUtils(workspace=WORKSPACE_DIR, min_node=MIN_NODE, package_manager=PACKAGE_MANAGER)


def post_processing():
    print('post processing env files')
    data = command_utils.read_file(".env.example")
    command_utils.create_file(".env" , data)
    return True


def execute_plan(plan: ProjectPlan):
    """Execute the project plan."""
    print("🎯 Executing project plan...")
    
    try:
        # if not command_utils.initialize_nextjs_project():
        #     return False    
        print("\n📁 Creating directories...")
        for directory in plan.directories:
            command_utils.create_directory(directory)
        
        print("\n📦 Installing packages...")
        for package in plan.packages:
            command_utils.install_package(package.name, package.dev)
        
  
        print("\n📝 Creating files...")
        for file_info in plan.files:
            command_utils.create_file(file_info.path, file_info.content)
        

        print("\n✅ Project plan executed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error executing plan: {str(e)}")
        return False


