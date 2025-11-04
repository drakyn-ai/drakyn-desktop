"""
Agent Management Tool - Allows agent to create and manage agents in the UI.

Agents are specialized assistants where the agent helps users handle specific missions.
Each agent has a name, mission, status, and activity feed.
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AgentArgs(BaseModel):
    """Arguments for agent operations"""
    action: str = Field(..., description="Action to perform: 'create', 'list', 'update', 'delete', 'analyze_status', or 'set_active'")
    name: str = Field(default="", description="Agent name (required for 'create' action)")
    mission: str = Field(default="", description="Brief description of the agent")
    status: str = Field(default="planning", description="Agent status: planning, researching, building, review, or complete")
    activity: str = Field(default="", description="Recent activity or update for the agent")
    agent_id: str = Field(default="", description="Agent ID (required for 'update', 'delete', 'analyze_status', and 'set_active' actions)")
    # Agent assessment fields
    agent_status: str = Field(default="", description="Agent's assessment: 'on_track', 'blocked', 'needs_info', 'at_risk', or 'complete'")
    agent_mission: str = Field(default="", description="Agent's brief analysis of agent status and next steps")
    estimated_completion: str = Field(default="", description="Agent's estimate for completion (e.g., '2 days', '1 week', 'unknown')")
    blockers: str = Field(default="", description="List of blockers or issues preventing progress")


class AgentTool:
    """
    Tool for managing agents in Drakyn Desktop.

    The agent uses this to:
    - Create new agents when the user starts something new
    - Update agent status and activity
    - List existing agents
    - Set the active agent for the conversation
    """

    name = "agent_manager"
    description = (
        "Create and manage agents in Drakyn Desktop. "
        "Use this when the user wants to start a new agent, track progress, organize their work, analyze status, or delete a agent. "
        "Actions: 'create' (new agent), 'list' (show all agents), 'update' (modify agent), "
        "'analyze_status' (assess agent health and provide estimate), 'delete' (remove agent), 'set_active' (switch active agent)"
    )

    # Projects are stored in the user's home directory
    USER_DIR = Path.home() / ".drakyn"
    AGENTS_FILE = USER_DIR / "agents.json"

    @staticmethod
    def _ensure_projects_file():
        """Ensure agents file exists"""
        AgentTool.USER_DIR.mkdir(exist_ok=True)

        if not AgentTool.AGENTS_FILE.exists():
            initial_data = {
                "agents": [],
                "active_agent_id": None,
                "last_updated": datetime.now().isoformat()
            }
            AgentTool.AGENTS_FILE.write_text(json.dumps(initial_data, indent=2))

    @staticmethod
    def _load_projects() -> Dict[str, Any]:
        """Load agents from file"""
        AgentTool._ensure_projects_file()
        try:
            return json.loads(AgentTool.AGENTS_FILE.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "agents": [],
                "active_agent_id": None,
                "last_updated": datetime.now().isoformat()
            }

    @staticmethod
    def _save_projects(data: Dict[str, Any]):
        """Save agents to file"""
        AgentTool._ensure_projects_file()
        data["last_updated"] = datetime.now().isoformat()
        AgentTool.AGENTS_FILE.write_text(json.dumps(data, indent=2))

    @staticmethod
    def _generate_agent_id() -> str:
        """Generate a unique agent ID"""
        import uuid
        return f"agent-{uuid.uuid4().hex[:8]}"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return JSON schema for this tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["create", "list", "update", "delete", "analyze_status", "set_active"],
                    "description": "Action to perform"
                },
                "name": {
                    "type": "string",
                    "description": "Agent name (required for 'create')"
                },
                "mission": {
                    "type": "string",
                    "description": "Brief description of what this agent is about"
                },
                "status": {
                    "type": "string",
                    "enum": ["planning", "researching", "building", "review", "complete"],
                    "default": "planning",
                    "description": "Current status of the agent"
                },
                "activity": {
                    "type": "string",
                    "description": "Recent activity or update for the agent"
                },
                "agent_id": {
                    "type": "string",
                    "description": "Agent ID (required for 'update' and 'set_active')"
                },
                "agent_status": {
                    "type": "string",
                    "enum": ["on_track", "blocked", "needs_info", "at_risk", "complete"],
                    "description": "Agent's assessment of agent health"
                },
                "agent_summary": {
                    "type": "string",
                    "description": "Agent's brief analysis of agent status and next steps"
                },
                "estimated_completion": {
                    "type": "string",
                    "description": "Agent's estimate for completion (e.g., '2 days', '1 week', 'unknown')"
                },
                "blockers": {
                    "type": "string",
                    "description": "List of blockers or issues preventing progress"
                }
            },
            "required": ["action"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent management operation.

        Args:
            args: Dictionary with action and optional agent details

        Returns:
            Result of the operation with UI update instructions
        """
        try:
            # Validate arguments
            validated = AgentArgs(**args)

            if validated.action == "create":
                return await AgentTool._create_project(validated)
            elif validated.action == "list":
                return await AgentTool._list_projects()
            elif validated.action == "update":
                return await AgentTool._update_project(validated)
            elif validated.action == "analyze_status":
                return await AgentTool._analyze_status(validated)
            elif validated.action == "delete":
                return await AgentTool._delete_project(validated.agent_id)
            elif validated.action == "set_active":
                return await AgentTool._set_active_project(validated.agent_id)
            else:
                return {
                    "error": f"Unknown action: {validated.action}",
                    "valid_actions": ["create", "list", "update", "analyze_status", "delete", "set_active"]
                }

        except Exception as e:
            return {
                "error": f"Failed to execute agent_manager tool: {str(e)}",
                "action": args.get("action", "unknown")
            }

    @staticmethod
    async def _create_project(args: AgentArgs) -> Dict[str, Any]:
        """Create a new agent"""
        try:
            if not args.name:
                return {
                    "error": "Agent name is required",
                    "action": "create"
                }

            # Load existing agents
            data = AgentTool._load_projects()

            # Create new agent
            agent = {
                "id": AgentTool._generate_agent_id(),
                "name": args.name.strip(),
                "mission": args.summary.strip() if args.summary else "No mission provided yet.",
                "status": args.status if args.status in ["planning", "researching", "building", "review", "complete"] else "planning",
                "activity": args.activity.strip() if args.activity else "Ready when you are.",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }

            # Add to agents list
            data["agents"].append(agent)

            # Set as active agent
            data["active_agent_id"] = agent["id"]

            # Save to file
            AgentTool._save_projects(data)

            return {
                "action": "create",
                "success": True,
                "agent": agent,
                "message": f"Created agent '{agent['name']}' and set it as active.",
                "ui_action": {
                    "type": "create_agent",
                    "agent": agent
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to create agent: {str(e)}",
                "action": "create"
            }

    @staticmethod
    async def _list_projects() -> Dict[str, Any]:
        """List all agents"""
        try:
            data = AgentTool._load_projects()

            return {
                "action": "list",
                "success": True,
                "agents": data["agents"],
                "active_agent_id": data.get("active_agent_id"),
                "count": len(data["agents"])
            }

        except Exception as e:
            return {
                "error": f"Failed to list agents: {str(e)}",
                "action": "list"
            }

    @staticmethod
    async def _update_project(args: AgentArgs) -> Dict[str, Any]:
        """Update an existing agent"""
        try:
            if not args.agent_id:
                return {
                    "error": "agent_id is required for update action",
                    "action": "update"
                }

            data = AgentTool._load_projects()

            # Find agent
            agent = None
            for p in data["agents"]:
                if p["id"] == args.agent_id:
                    agent = p
                    break

            if not agent:
                return {
                    "error": f"Agent with id '{args.agent_id}' not found",
                    "action": "update"
                }

            # Update fields
            if args.name:
                agent["name"] = args.name.strip()
            if args.summary:
                agent["mission"] = args.summary.strip()
            if args.status:
                agent["status"] = args.status
            if args.activity:
                agent["activity"] = args.activity.strip()

            agent["last_updated"] = datetime.now().isoformat()

            # Save changes
            AgentTool._save_projects(data)

            return {
                "action": "update",
                "success": True,
                "agent": agent,
                "message": f"Updated agent '{agent['name']}'",
                "ui_action": {
                    "type": "update_agent",
                    "agent": agent
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to update agent: {str(e)}",
                "action": "update"
            }

    @staticmethod
    async def _set_active_project(agent_id: str) -> Dict[str, Any]:
        """Set the active agent"""
        try:
            if not agent_id:
                return {
                    "error": "agent_id is required",
                    "action": "set_active"
                }

            data = AgentTool._load_projects()

            # Verify agent exists
            agent_exists = any(p["id"] == agent_id for p in data["agents"])

            if not agent_exists:
                return {
                    "error": f"Agent with id '{agent_id}' not found",
                    "action": "set_active"
                }

            # Set as active
            data["active_agent_id"] = agent_id
            AgentTool._save_projects(data)

            return {
                "action": "set_active",
                "success": True,
                "agent_id": agent_id,
                "message": f"Set active agent to {agent_id}",
                "ui_action": {
                    "type": "set_active_agent",
                    "agent_id": agent_id
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to set active agent: {str(e)}",
                "action": "set_active"
            }

    @staticmethod
    async def _analyze_status(args: AgentArgs) -> Dict[str, Any]:
        """Analyze and update agent status with agent assessment"""
        try:
            if not args.agent_id:
                return {
                    "error": "agent_id is required for analyze_status action",
                    "action": "analyze_status"
                }

            # Validate required assessment fields
            if not args.agent_status or not args.agent_summary:
                return {
                    "error": "agent_status and agent_summary are required for status analysis",
                    "action": "analyze_status"
                }

            data = AgentTool._load_projects()

            # Find agent
            agent = None
            for p in data["agents"]:
                if p["id"] == args.agent_id:
                    agent = p
                    break

            if not agent:
                return {
                    "error": f"Agent with id '{args.agent_id}' not found",
                    "action": "analyze_status"
                }

            # Update agent with agent assessment
            agent["agent_status"] = args.agent_status
            agent["agent_summary"] = args.agent_summary
            agent["estimated_completion"] = args.estimated_completion or "Unknown"
            agent["blockers"] = args.blockers or "None identified"
            agent["last_analyzed"] = datetime.now().isoformat()
            agent["last_updated"] = datetime.now().isoformat()

            # Save changes
            AgentTool._save_projects(data)

            return {
                "action": "analyze_status",
                "success": True,
                "agent": agent,
                "message": f"Updated status analysis for '{agent['name']}'",
                "ui_action": {
                    "type": "update_agent",
                    "agent": agent
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to analyze agent status: {str(e)}",
                "action": "analyze_status"
            }

    @staticmethod
    async def _delete_project(agent_id: str) -> Dict[str, Any]:
        """Delete a agent"""
        try:
            if not agent_id:
                return {
                    "error": "agent_id is required for delete action",
                    "action": "delete"
                }

            data = AgentTool._load_projects()

            # Find agent to delete
            agent_to_delete = None
            for p in data["agents"]:
                if p["id"] == agent_id:
                    agent_to_delete = p
                    break

            if not agent_to_delete:
                return {
                    "error": f"Agent with id '{agent_id}' not found",
                    "action": "delete"
                }

            # Remove agent from list
            data["agents"] = [p for p in data["agents"] if p["id"] != agent_id]

            # If this was the active agent, clear active_agent_id or set to another agent
            if data.get("active_agent_id") == agent_id:
                # Set to first remaining agent or None
                data["active_agent_id"] = data["agents"][0]["id"] if data["agents"] else None

            # Save changes
            AgentTool._save_projects(data)

            return {
                "action": "delete",
                "success": True,
                "deleted_agent": agent_to_delete,
                "message": f"Deleted agent '{project_to_delete['name']}'",
                "new_active_agent_id": data.get("active_agent_id"),
                "ui_action": {
                    "type": "delete_agent",
                    "agent_id": agent_id,
                    "new_active_agent_id": data.get("active_agent_id")
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to delete agent: {str(e)}",
                "action": "delete"
            }
