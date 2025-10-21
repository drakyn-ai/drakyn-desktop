"""
User Context Tool - Allows agent to read and update its memory about the user.

The agent maintains a plain text file with information about the user's life,
preferences, patterns, and learned context. This tool provides read/write access.
"""
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class UserContextArgs(BaseModel):
    """Arguments for user context operations"""
    action: str = Field(..., description="Action to perform: 'read' or 'update'")
    content: str = Field(default="", description="New content when action is 'update'")
    append: bool = Field(default=False, description="If true, append to existing content instead of replacing")


class UserContextTool:
    """
    Tool for managing user context in plain text format.

    The agent uses this to:
    - Read what it knows about the user
    - Update its knowledge when learning new information
    - Keep track of what suggestions work well
    """

    name = "user_context"
    description = (
        "Read or update your memory about the user. "
        "The user context is a plain text file where you store everything you learn "
        "about the user's life, preferences, patterns, and what kinds of help they find useful. "
        "Use 'read' to see what you currently know, 'update' to rewrite or append new information."
    )

    # Class-level paths
    USER_DIR = Path.home() / ".drakyn"
    CONTEXT_FILE = USER_DIR / "user_context.txt"

    @staticmethod
    def _ensure_context_file():
        """Ensure context file exists with template"""
        UserContextTool.USER_DIR.mkdir(exist_ok=True)

        if not UserContextTool.CONTEXT_FILE.exists():
            template = """# User Context

About the User:
[The agent will learn about you as you interact]

Preferences:
- Proactive level: moderate (a few check-ins per day)
- Notification style: Brief and actionable
- Quiet hours: 10pm - 7am (no notifications)

What Has Been Helpful:
[The agent will learn what kinds of suggestions you find useful]

What Hasn't Been Helpful:
[The agent will learn what to avoid]

Recent Context:
[The agent will note recent events and patterns]

---
Last updated: {timestamp}
""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

            UserContextTool.CONTEXT_FILE.write_text(template)

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return JSON schema for this tool's parameters"""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["read", "update"],
                    "description": "Action to perform: 'read' to see current context, 'update' to modify it"
                },
                "content": {
                    "type": "string",
                    "description": "New content when action is 'update' (required for update action)"
                },
                "append": {
                    "type": "boolean",
                    "default": False,
                    "description": "If true, append content to existing file instead of replacing it"
                }
            },
            "required": ["action"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute user context operation.

        Args:
            args: Dictionary with 'action' and optionally 'content' and 'append'

        Returns:
            Result of the operation
        """
        try:
            # Validate arguments
            validated = UserContextArgs(**args)

            if validated.action == "read":
                return await UserContextTool._read_context()
            elif validated.action == "update":
                return await UserContextTool._update_context(validated.content, validated.append)
            else:
                return {
                    "error": f"Unknown action: {validated.action}",
                    "valid_actions": ["read", "update"]
                }

        except Exception as e:
            return {
                "error": f"Failed to execute user_context tool: {str(e)}",
                "action": args.get("action", "unknown")
            }

    @staticmethod
    async def _read_context() -> Dict[str, Any]:
        """Read current user context"""
        try:
            UserContextTool._ensure_context_file()

            content = UserContextTool.CONTEXT_FILE.read_text()

            return {
                "action": "read",
                "content": content,
                "file_path": str(UserContextTool.CONTEXT_FILE),
                "last_modified": datetime.fromtimestamp(
                    UserContextTool.CONTEXT_FILE.stat().st_mtime
                ).strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            return {
                "error": f"Failed to read user context: {str(e)}",
                "file_path": str(UserContextTool.CONTEXT_FILE)
            }

    @staticmethod
    async def _update_context(content: str, append: bool = False) -> Dict[str, Any]:
        """Update user context"""
        try:
            if not content:
                return {
                    "error": "Content is required for update action",
                    "action": "update"
                }

            # Ensure directory exists
            UserContextTool._ensure_context_file()

            if append:
                # Read existing content
                existing = ""
                if UserContextTool.CONTEXT_FILE.exists():
                    existing = UserContextTool.CONTEXT_FILE.read_text()

                # Append new content
                new_content = existing + "\n\n" + content
                new_content += f"\n\n---\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                # Replace entire content
                new_content = content
                new_content += f"\n\n---\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Write to file
            UserContextTool.CONTEXT_FILE.write_text(new_content)

            return {
                "action": "update",
                "success": True,
                "append": append,
                "file_path": str(UserContextTool.CONTEXT_FILE),
                "content_length": len(new_content),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            return {
                "error": f"Failed to update user context: {str(e)}",
                "file_path": str(UserContextTool.CONTEXT_FILE)
            }
