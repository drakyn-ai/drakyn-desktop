"""
MCP Manager Tool - Discovers and installs MCP servers dynamically.
Allows the agent to extend its own capabilities by installing new tools.
"""
import logging
from typing import Dict, Any, List
import subprocess
import json
from pathlib import Path
import requests

logger = logging.getLogger(__name__)

class MCPManagerTool:
    """Tool for discovering and installing MCP servers."""

    name = "mcp_manager"
    description = "Discover, search, and install Python MCP servers to extend agent capabilities. Only supports Python packages from PyPI or GitHub (not NPM/Node.js)."

    # Directory where MCP servers are installed
    MCP_SERVERS_DIR = Path.home() / ".drakyn" / "mcp_servers"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return the tool schema for the agent."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "install", "list_installed", "request_permission"],
                    "description": "Action to perform: search for MCP servers, install one, list installed servers, or request user permission"
                },
                "query": {
                    "type": "string",
                    "description": "Search query for finding MCP servers (used with 'search' action)"
                },
                "package_name": {
                    "type": "string",
                    "description": "NPM package name or GitHub URL to install (used with 'install' action)"
                },
                "description": {
                    "type": "string",
                    "description": "Description of what you want to install (used with 'request_permission' action)"
                }
            },
            "required": ["action"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute MCP manager action."""
        action = args.get("action")

        try:
            if action == "search":
                return await MCPManagerTool._search_mcp_servers(args.get("query", ""))

            elif action == "list_installed":
                return await MCPManagerTool._list_installed_servers()

            elif action == "request_permission":
                # This returns a special response that the agent should use
                # to ask the user for permission
                return {
                    "permission_required": True,
                    "action_requested": "install_mcp_server",
                    "description": args.get("description", "Install an MCP server"),
                    "message": "I found an MCP server that can help with this task. Would you like me to install it?",
                    "next_step": "After user approval, call this tool again with action='install' and package_name"
                }

            elif action == "install":
                package_name = args.get("package_name")
                if not package_name:
                    return {"error": "package_name is required for install action"}

                return await MCPManagerTool._install_mcp_server(package_name)

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"MCP Manager error: {str(e)}")
            return {"error": f"MCP Manager error: {str(e)}"}

    @staticmethod
    async def _search_mcp_servers(query: str) -> Dict[str, Any]:
        """
        Search for Python MCP servers on PyPI.

        Returns results with package name, description, and installation info.
        """
        logger.info(f"Searching for Python MCP servers: {query}")

        results = []

        try:
            # Search PyPI for Python MCP servers
            pypi_url = "https://pypi.org/search/"
            search_query = f"mcp {query}"

            logger.info(f"Searching PyPI: {search_query}")

            # PyPI doesn't have a JSON API for search, so we return guidance
            # The agent should use web_search tool instead

            return {
                "query": query,
                "num_results": 0,
                "results": [],
                "note": "PyPI doesn't provide a search API. Use the 'web_search' tool to search for Python MCP servers on GitHub or PyPI.",
                "guidance": [
                    f"Try: web_search with query 'python mcp server {query} github'",
                    f"Look for GitHub repositories with 'mcp-server-{query}' or '{query}-mcp-server'",
                    "Python MCP servers typically have a setup.py or pyproject.toml file",
                    "Installation is usually via: pip install <package-name> or pip install -e <github-url>"
                ]
            }

        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return {
                "error": f"Search failed: {str(e)}",
                "fallback": "Use web_search tool to find Python MCP servers on:\n- https://github.com/topics/mcp-server\n- https://github.com/search?q=mcp+server+python"
            }

    @staticmethod
    async def _install_mcp_server(package_name: str) -> Dict[str, Any]:
        """
        Install a Python MCP server from PyPI or GitHub.

        Args:
            package_name: PyPI package name (e.g., "mcp-server-slack")
                         or GitHub URL (e.g., "https://github.com/user/mcp-server-slack")
        """
        logger.info(f"Installing Python MCP server: {package_name}")

        try:
            # Create MCP servers directory if it doesn't exist
            MCPManagerTool.MCP_SERVERS_DIR.mkdir(parents=True, exist_ok=True)

            # Determine installation method
            if package_name.startswith("http://") or package_name.startswith("https://"):
                # GitHub URL - clone and install
                repo_name = package_name.split("/")[-1].replace(".git", "")
                install_dir = MCPManagerTool.MCP_SERVERS_DIR / repo_name

                if install_dir.exists():
                    return {
                        "already_installed": True,
                        "message": f"Python MCP server '{repo_name}' is already installed",
                        "path": str(install_dir)
                    }

                # Clone repository
                logger.info(f"Cloning {package_name}")
                result = subprocess.run(
                    ["git", "clone", package_name, str(install_dir)],
                    capture_output=True,
                    text=True,
                    timeout=60
                )

                if result.returncode != 0:
                    return {"error": f"Git clone failed: {result.stderr}"}

                # Only support Python packages - check for requirements.txt or setup.py
                if (install_dir / "requirements.txt").exists():
                    # Install Python dependencies
                    logger.info("Installing Python dependencies from requirements.txt")
                    result = subprocess.run(
                        ["pip", "install", "-r", "requirements.txt"],
                        cwd=install_dir,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )

                    if result.returncode != 0:
                        return {"error": f"pip install failed: {result.stderr}"}

                elif (install_dir / "setup.py").exists() or (install_dir / "pyproject.toml").exists():
                    # Install package in editable mode
                    logger.info("Installing Python package in editable mode")
                    result = subprocess.run(
                        ["pip", "install", "-e", str(install_dir)],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )

                    if result.returncode != 0:
                        return {"error": f"pip install failed: {result.stderr}"}
                else:
                    return {
                        "error": "Not a Python package. Only Python MCP servers are supported (must have requirements.txt, setup.py, or pyproject.toml)"
                    }

                return {
                    "success": True,
                    "message": f"Successfully installed Python MCP server '{repo_name}'",
                    "path": str(install_dir),
                    "type": "python",
                    "next_steps": "The MCP server is installed. Restart the MCP service to load it."
                }

            else:
                # PyPI package - install via pip
                logger.info(f"Installing Python package from PyPI: {package_name}")
                result = subprocess.run(
                    ["pip", "install", package_name],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode != 0:
                    return {"error": f"pip install failed: {result.stderr}"}

                return {
                    "success": True,
                    "message": f"Successfully installed Python MCP server '{package_name}' from PyPI",
                    "type": "python",
                    "next_steps": "The MCP server is installed. Restart the MCP service to load it."
                }

        except subprocess.TimeoutExpired:
            return {"error": "Installation timed out"}
        except Exception as e:
            logger.error(f"Installation failed: {str(e)}")
            return {"error": f"Installation failed: {str(e)}"}

    @staticmethod
    async def _list_installed_servers() -> Dict[str, Any]:
        """List all installed MCP servers."""
        try:
            if not MCPManagerTool.MCP_SERVERS_DIR.exists():
                return {
                    "installed_servers": [],
                    "count": 0
                }

            installed = []
            for server_dir in MCPManagerTool.MCP_SERVERS_DIR.iterdir():
                if server_dir.is_dir():
                    # Only list Python packages
                    info = {
                        "name": server_dir.name,
                        "path": str(server_dir),
                        "type": "python"
                    }

                    # Try to get info from setup.py or pyproject.toml
                    setup_py = server_dir / "setup.py"
                    pyproject_toml = server_dir / "pyproject.toml"

                    if setup_py.exists() or pyproject_toml.exists() or (server_dir / "requirements.txt").exists():
                        info["description"] = "Python MCP server"
                        installed.append(info)

            return {
                "installed_servers": installed,
                "count": len(installed)
            }

        except Exception as e:
            logger.error(f"Failed to list installed servers: {str(e)}")
            return {"error": f"Failed to list servers: {str(e)}"}
