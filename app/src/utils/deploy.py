import os
from src.utils.command_utils import CommandUtils
from configs import WORKSPACE_DIR, MIN_NODE, PACKAGE_MANAGER

command_utils = CommandUtils(workspace=WORKSPACE_DIR, min_node=MIN_NODE, package_manager=PACKAGE_MANAGER)
def push_workspace_to_github(branch_name, repo_url=None, commit_message="Add workspace files"):
    """
    Push workspace folder to GitHub on a new branch
    
    Args:
        branch_name: Name of the branch to create
        repo_url: GitHub repository URL (optional if already configured)
        commit_message: Commit message for the changes
    """
    workspace_path = os.path.join(os.getcwd(), "workspace")
    
    if not os.path.exists(workspace_path):
        print("Error: workspace folder not found")
        return False
    
    try:
        # Change to workspace directory
        os.chdir(workspace_path)
        
        # Initialize git if not already initialized
        stdout, stderr = command_utils.run_command(["git", "status"], cwd=workspace_path)
        if "not a git repository" in stderr:
            print("Initializing git repository...")
            command_utils.run_command(["git", "init"], cwd=workspace_path)
            
            # Add remote if repo_url is provided
            if repo_url:
                command_utils.run_command(["git", "remote", "add", "origin", repo_url], cwd=workspace_path)
        
        # Create and checkout new branch
        print(f"Creating and switching to branch: {branch_name}")
        command_utils.run_command(["git", "checkout", "-b", branch_name], cwd=workspace_path)
        
        # Add all files
        print("Adding all files...")
        command_utils.run_command(["git", "add", "."], cwd=workspace_path)
        
        # Commit changes
        print("Committing changes...")
        command_utils.run_command(["git", "commit", "-m", commit_message], cwd=workspace_path)
        
        # Push to GitHub
        print(f"Pushing to GitHub on branch {branch_name}...")
        stdout, stderr = command_utils.run_command(["git", "push", "-u", "origin", branch_name], cwd=workspace_path)
        
        if stderr and "error" in stderr.lower():
            print(f"Push failed: {stderr}")
            return False
        else:
            print(f"Successfully pushed workspace to GitHub on branch {branch_name}")
            return True
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Go back to original directory
        os.chdir(os.path.dirname(workspace_path))


