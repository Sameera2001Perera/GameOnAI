import re
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List


class CommandUtils():

    def __init__(self, workspace : Path, min_node : tuple, package_manager : str):
        self.workspace = workspace
        self.min_node = min_node
        self.package_manager = package_manager
    
    def parse_semver(self, v: str):
        m = re.match(r"v?(\d+)\.(\d+)\.(\d+)", v.strip())
        return tuple(map(int, m.groups())) if m else (0, 0, 0)

    def ensure(self, cmd: str):
        if shutil.which(cmd) is None:
            raise Exception(f"'{cmd}' not found on PATH.")

    def ensure_node_version(self, ):
        try:
            out = subprocess.check_output(["node", "-v"], text=True)
            print(f"✓ Found Node.js version: {out.strip()}")
        except Exception as e:
            raise Exception(f"Could not run 'node -v' ({e}).")
        if self.parse_semver(out) < self.min_node:
            need = ".".join(map(str, self.min_node))
            raise Exception(f"Node.js {need}+ required. Found {out.strip()}.")

    def run_command(self, cmd, cwd=None):
        print("➜", " ".join(cmd))
        try:
            result = subprocess.run(cmd, check=True, cwd=cwd, capture_output=True, text=True)
            return result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return e.stdout, e.stderr
    
    def move_file(self, source_path, destination_path):
        try:
            shutil.copytree(source_path, destination_path)
            print(f"Successfully copied workspace folder from {source_path} to {destination_path}")
        except FileExistsError:
            print("Destination folder already exists. Use shutil.copytree with dirs_exist_ok=True to overwrite:")
            shutil.copytree(source_path, destination_path, dirs_exist_ok=True)
            print("Folder copied with overwrite")
        except FileNotFoundError:
            print(f"Source folder not found at {source_path}")
        except Exception as e:
            print(f"An error occurred: {e}")
        
    def initialize_nextjs_project(self):
        """Initialize a clean Next.js project with TypeScript and Tailwind CSS v3 (stable)."""
        print("🔧 Initializing Next.js project...")
        try:
            self.ensure("node")
            self.ensure("npx")
            self.ensure_node_version()

            if self.workspace.exists():
                print(f"🗑️  Removing existing workspace: {self.workspace}")
                shutil.rmtree(self.workspace)

            print(f"📁 Creating workspace directory: {self.workspace}")
            self.workspace.mkdir(parents=True, exist_ok=True)

            pm_flag = {
                "npm": "--use-npm",
                "pnpm": "--use-pnpm", 
                "yarn": "--use-yarn",
                "bun": "--use-bun",
            }[self.package_manager]

            # Create Next.js app WITHOUT Tailwind to avoid v4 issues
            cna = [
                "npx", "create-next-app@latest", ".",
                "--typescript", "--eslint",
                "--app", "--import-alias", "@/*",
                pm_flag ,"--yes", 
            ]
            
            print("🚀 Running create-next-app...")
            self.run_command(cna, cwd=str(self.workspace))
            
            
            print("📦 Installing Tailwind CSS v3...")
            install_cmd = [
                self.package_manager, "install", "-D", 
                "tailwindcss@^3.4.0", "postcss", "autoprefixer"
            ]
            self.run_command(install_cmd, cwd=str(self.workspace))
            
  
            print("⚙️  Initializing Tailwind configuration...")
            self.run_command(["npx", "tailwindcss", "init", "-p"], cwd=str(self.workspace))
            

            
            print("✅ Next.js + Tailwind CSS v3 initialized successfully!")
            print("📝 Tailwind CSS is configured with:")
            print("   - TypeScript support")
            print("   - App Router")
            print("   - Source directory structure")
            print("   - Import alias (@/*)")
            print("   - PostCSS configuration")
            print("   - Tailwind v3 (stable) with proper content paths")
            
            return True

        except Exception as e:
            print(f"❌ Error initializing Next.js project: {str(e)}")
            return False


    def create_file(self, path: str, content: str):
        """Create a file with the specified content."""
        print(f"📝 Creating file: {path}")
        try:
            full_path = self.workspace / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"✅ Created file: {path}")
            return True
        except Exception as e:
            print(f"❌ Error creating file {path}: {str(e)}")
            return False

    def create_directory(self, dir_path: str):
        """Create a directory."""
        
        try:
            full_path = self.workspace / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created directory: {full_path}")
            return True
        except Exception as e:
            print(f"❌ Error creating directory {dir_path}: {str(e)}")
            return False

    def install_package(self, package_name: str, dev: bool = False):
        """Install an npm package."""
        print(f"📦 Installing package: {package_name}")
        try:
            cmd = [self.package_manager, "install", package_name]
            if dev:
                cmd.append("--save-dev")
            
            self.run_command(cmd, cwd=str(self.workspace))
            print(f"✅ Installed package: {package_name}")
            return True
        except Exception as e:
            print(f"❌ Error installing package {package_name}: {str(e)}")
            return False
        
    def read_file(self, file_path: str) -> str:
        """Read and return the content of a file inside the workspace."""
        print(f"📖 Reading file: {file_path}")
        full_path = self.workspace / file_path
        print("full path : {}")
        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        with open(full_path, 'r', encoding='utf-8') as f:
            data = f.read()
        print(f"✅ Read {len(data)} chars from {file_path}")
        return data
    
    def remove_file(self, path : str) :
        print("Removing file !!!")
        full_path = self.workspace / path
        if not full_path.exists():
            raise FileNotFoundError(f"❌ File not found:{path}")
        try:
            full_path.unlink()
            print("🗑️ File deleted successfully")
        except PermissionError:
            print("🚫 Permission denied")

        
    def _has_script(self, name: str) -> bool:
        """Check if package.json contains the given script."""
        pkg = self.workspace / "package.json"
        try:
            with open(pkg, "r", encoding="utf-8") as f:
                data = json.load(f)
            return bool(data.get("scripts", {}).get(name))
        except Exception:
            # If anything goes wrong, don't hard fail—let run attempt anyway
            return False

    
    def run_script(self, script: str, extra_args: Optional[List[str]] = None):

        print(f"🏃 Running script: {script}")
        try:
            pm = self.package_manager
            extra_args = extra_args or []

            if pm == "npm":
                cmd = ["npm", "run", script] + ["--"] + extra_args if extra_args else ["npm", "run", script]
            elif pm == "pnpm":
                cmd = ["pnpm", "run", script] + extra_args
            elif pm == "yarn":

                cmd = ["yarn", script] + extra_args
            elif pm == "bun":
                cmd = ["bun", "run", script] + extra_args
            else:
                raise Exception(f"Unsupported package manager: {pm}")

            if not self._has_script(script):
                print(f"⚠️  Warning: script '{script}' not found in package.json. Attempting to run anyway.")

            out , err = self.run_command(cmd, cwd=str(self.workspace))
            print(f"✅ Script '{script}' finished")
            return out, err
        except Exception as e:
            print(f"❌ Error running script '{script}': {str(e)}")
            raise
