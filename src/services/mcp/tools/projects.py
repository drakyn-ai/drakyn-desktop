"""
Project Management Tool - Allows agent to create and manage projects in the UI.

Projects are workspaces where the agent helps users track and organize tasks.
Each project has a name, summary, status, and activity feed.
"""
import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class ProjectArgs(BaseModel):
    """Arguments for project operations"""
    action: str = Field(..., description="Action to perform: 'create', 'list', 'update', 'delete', 'analyze_status', or 'set_active'")
    name: str = Field(default="", description="Project name (required for 'create' action)")
    summary: str = Field(default="", description="Brief description of the project")
    status: str = Field(default="planning", description="Project status: planning, researching, building, review, or complete")
    activity: str = Field(default="", description="Recent activity or update for the project")
    project_id: str = Field(default="", description="Project ID (required for 'update', 'delete', 'analyze_status', and 'set_active' actions)")
    # Agent assessment fields
    agent_status: str = Field(default="", description="Agent's assessment: 'on_track', 'blocked', 'needs_info', 'at_risk', or 'complete'")
    agent_summary: str = Field(default="", description="Agent's brief analysis of project status and next steps")
    estimated_completion: str = Field(default="", description="Agent's estimate for completion (e.g., '2 days', '1 week', 'unknown')")
    blockers: str = Field(default="", description="List of blockers or issues preventing progress")


class ProjectTool:
    """
    Tool for managing projects in Drakyn Desktop.

    The agent uses this to:
    - Create new projects when the user starts something new
    - Update project status and activity
    - List existing projects
    - Set the active project for the conversation
    """

    name = "project_manager"
    description = (
        "Create and manage projects in Drakyn Desktop. "
        "Use this when the user wants to start a new project, track progress, organize their work, analyze status, or delete a project. "
        "Actions: 'create' (new project), 'list' (show all projects), 'update' (modify project), "
        "'analyze_status' (assess project health and provide estimate), 'delete' (remove project), 'set_active' (switch active project)"
    )

    # Projects are stored in the user's home directory
    USER_DIR = Path.home() / ".drakyn"
    PROJECTS_FILE = USER_DIR / "projects.json"

    @staticmethod
    def _ensure_projects_file():
        """Ensure projects file exists"""
        ProjectTool.USER_DIR.mkdir(exist_ok=True)

        if not ProjectTool.PROJECTS_FILE.exists():
            initial_data = {
                "projects": [],
                "active_project_id": None,
                "last_updated": datetime.now().isoformat()
            }
            ProjectTool.PROJECTS_FILE.write_text(json.dumps(initial_data, indent=2))

    @staticmethod
    def _load_projects() -> Dict[str, Any]:
        """Load projects from file"""
        ProjectTool._ensure_projects_file()
        try:
            return json.loads(ProjectTool.PROJECTS_FILE.read_text())
        except (json.JSONDecodeError, FileNotFoundError):
            return {
                "projects": [],
                "active_project_id": None,
                "last_updated": datetime.now().isoformat()
            }

    @staticmethod
    def _save_projects(data: Dict[str, Any]):
        """Save projects to file"""
        ProjectTool._ensure_projects_file()
        data["last_updated"] = datetime.now().isoformat()
        ProjectTool.PROJECTS_FILE.write_text(json.dumps(data, indent=2))

    @staticmethod
    def _generate_project_id() -> str:
        """Generate a unique project ID"""
        import uuid
        return f"project-{uuid.uuid4().hex[:8]}"

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
                    "description": "Project name (required for 'create')"
                },
                "summary": {
                    "type": "string",
                    "description": "Brief description of what this project is about"
                },
                "status": {
                    "type": "string",
                    "enum": ["planning", "researching", "building", "review", "complete"],
                    "default": "planning",
                    "description": "Current status of the project"
                },
                "activity": {
                    "type": "string",
                    "description": "Recent activity or update for the project"
                },
                "project_id": {
                    "type": "string",
                    "description": "Project ID (required for 'update' and 'set_active')"
                },
                "agent_status": {
                    "type": "string",
                    "enum": ["on_track", "blocked", "needs_info", "at_risk", "complete"],
                    "description": "Agent's assessment of project health"
                },
                "agent_summary": {
                    "type": "string",
                    "description": "Agent's brief analysis of project status and next steps"
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
        Execute project management operation.

        Args:
            args: Dictionary with action and optional project details

        Returns:
            Result of the operation with UI update instructions
        """
        try:
            # Validate arguments
            validated = ProjectArgs(**args)

            if validated.action == "create":
                return await ProjectTool._create_project(validated)
            elif validated.action == "list":
                return await ProjectTool._list_projects()
            elif validated.action == "update":
                return await ProjectTool._update_project(validated)
            elif validated.action == "analyze_status":
                return await ProjectTool._analyze_status(validated)
            elif validated.action == "delete":
                return await ProjectTool._delete_project(validated.project_id)
            elif validated.action == "set_active":
                return await ProjectTool._set_active_project(validated.project_id)
            else:
                return {
                    "error": f"Unknown action: {validated.action}",
                    "valid_actions": ["create", "list", "update", "analyze_status", "delete", "set_active"]
                }

        except Exception as e:
            return {
                "error": f"Failed to execute project_manager tool: {str(e)}",
                "action": args.get("action", "unknown")
            }

    @staticmethod
    async def _create_project(args: ProjectArgs) -> Dict[str, Any]:
        """Create a new project"""
        try:
            if not args.name:
                return {
                    "error": "Project name is required",
                    "action": "create"
                }

            # Load existing projects
            data = ProjectTool._load_projects()

            # Create new project
            project = {
                "id": ProjectTool._generate_project_id(),
                "name": args.name.strip(),
                "summary": args.summary.strip() if args.summary else "No summary provided yet.",
                "status": args.status if args.status in ["planning", "researching", "building", "review", "complete"] else "planning",
                "activity": args.activity.strip() if args.activity else "Ready when you are.",
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat()
            }

            # Add to projects list
            data["projects"].append(project)

            # Set as active project
            data["active_project_id"] = project["id"]

            # Save to file
            ProjectTool._save_projects(data)

            return {
                "action": "create",
                "success": True,
                "project": project,
                "message": f"Created project '{project['name']}' and set it as active.",
                "ui_action": {
                    "type": "create_project",
                    "project": project
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to create project: {str(e)}",
                "action": "create"
            }

    @staticmethod
    async def _list_projects() -> Dict[str, Any]:
        """List all projects"""
        try:
            data = ProjectTool._load_projects()

            return {
                "action": "list",
                "success": True,
                "projects": data["projects"],
                "active_project_id": data.get("active_project_id"),
                "count": len(data["projects"])
            }

        except Exception as e:
            return {
                "error": f"Failed to list projects: {str(e)}",
                "action": "list"
            }

    @staticmethod
    async def _update_project(args: ProjectArgs) -> Dict[str, Any]:
        """Update an existing project"""
        try:
            if not args.project_id:
                return {
                    "error": "project_id is required for update action",
                    "action": "update"
                }

            data = ProjectTool._load_projects()

            # Find project
            project = None
            for p in data["projects"]:
                if p["id"] == args.project_id:
                    project = p
                    break

            if not project:
                return {
                    "error": f"Project with id '{args.project_id}' not found",
                    "action": "update"
                }

            # Update fields
            if args.name:
                project["name"] = args.name.strip()
            if args.summary:
                project["summary"] = args.summary.strip()
            if args.status:
                project["status"] = args.status
            if args.activity:
                project["activity"] = args.activity.strip()

            project["last_updated"] = datetime.now().isoformat()

            # Save changes
            ProjectTool._save_projects(data)

            return {
                "action": "update",
                "success": True,
                "project": project,
                "message": f"Updated project '{project['name']}'",
                "ui_action": {
                    "type": "update_project",
                    "project": project
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to update project: {str(e)}",
                "action": "update"
            }

    @staticmethod
    async def _set_active_project(project_id: str) -> Dict[str, Any]:
        """Set the active project"""
        try:
            if not project_id:
                return {
                    "error": "project_id is required",
                    "action": "set_active"
                }

            data = ProjectTool._load_projects()

            # Verify project exists
            project_exists = any(p["id"] == project_id for p in data["projects"])

            if not project_exists:
                return {
                    "error": f"Project with id '{project_id}' not found",
                    "action": "set_active"
                }

            # Set as active
            data["active_project_id"] = project_id
            ProjectTool._save_projects(data)

            return {
                "action": "set_active",
                "success": True,
                "project_id": project_id,
                "message": f"Set active project to {project_id}",
                "ui_action": {
                    "type": "set_active_project",
                    "project_id": project_id
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to set active project: {str(e)}",
                "action": "set_active"
            }

    @staticmethod
    async def _analyze_status(args: ProjectArgs) -> Dict[str, Any]:
        """Analyze and update project status with agent assessment"""
        try:
            if not args.project_id:
                return {
                    "error": "project_id is required for analyze_status action",
                    "action": "analyze_status"
                }

            # Validate required assessment fields
            if not args.agent_status or not args.agent_summary:
                return {
                    "error": "agent_status and agent_summary are required for status analysis",
                    "action": "analyze_status"
                }

            data = ProjectTool._load_projects()

            # Find project
            project = None
            for p in data["projects"]:
                if p["id"] == args.project_id:
                    project = p
                    break

            if not project:
                return {
                    "error": f"Project with id '{args.project_id}' not found",
                    "action": "analyze_status"
                }

            # Update project with agent assessment
            project["agent_status"] = args.agent_status
            project["agent_summary"] = args.agent_summary
            project["estimated_completion"] = args.estimated_completion or "Unknown"
            project["blockers"] = args.blockers or "None identified"
            project["last_analyzed"] = datetime.now().isoformat()
            project["last_updated"] = datetime.now().isoformat()

            # Save changes
            ProjectTool._save_projects(data)

            return {
                "action": "analyze_status",
                "success": True,
                "project": project,
                "message": f"Updated status analysis for '{project['name']}'",
                "ui_action": {
                    "type": "update_project",
                    "project": project
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to analyze project status: {str(e)}",
                "action": "analyze_status"
            }

    @staticmethod
    async def _delete_project(project_id: str) -> Dict[str, Any]:
        """Delete a project"""
        try:
            if not project_id:
                return {
                    "error": "project_id is required for delete action",
                    "action": "delete"
                }

            data = ProjectTool._load_projects()

            # Find project to delete
            project_to_delete = None
            for p in data["projects"]:
                if p["id"] == project_id:
                    project_to_delete = p
                    break

            if not project_to_delete:
                return {
                    "error": f"Project with id '{project_id}' not found",
                    "action": "delete"
                }

            # Remove project from list
            data["projects"] = [p for p in data["projects"] if p["id"] != project_id]

            # If this was the active project, clear active_project_id or set to another project
            if data.get("active_project_id") == project_id:
                # Set to first remaining project or None
                data["active_project_id"] = data["projects"][0]["id"] if data["projects"] else None

            # Save changes
            ProjectTool._save_projects(data)

            return {
                "action": "delete",
                "success": True,
                "deleted_project": project_to_delete,
                "message": f"Deleted project '{project_to_delete['name']}'",
                "new_active_project_id": data.get("active_project_id"),
                "ui_action": {
                    "type": "delete_project",
                    "project_id": project_id,
                    "new_active_project_id": data.get("active_project_id")
                }
            }

        except Exception as e:
            return {
                "error": f"Failed to delete project: {str(e)}",
                "action": "delete"
            }
