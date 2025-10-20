"""
Gmail MCP Tool - Provides email reading and sending capabilities via Gmail API.
Uses mcp-gmail library for Gmail integration.
"""
import logging
from typing import Dict, Any, List
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class GmailTool:
    """Tool for Gmail operations."""

    name = "gmail"
    description = "Search, read, and send Gmail messages. Supports searching by query, reading email content, and sending new emails."

    # Credentials path
    CREDENTIALS_DIR = Path(__file__).parent.parent / "credentials"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return the JSON schema for Gmail tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "read", "send"],
                    "description": "Action to perform: search for emails, read a specific email, or send a new email"
                },
                "query": {
                    "type": "string",
                    "description": "Gmail search query (for search action). Examples: 'is:unread', 'from:sender@example.com', 'subject:meeting'"
                },
                "message_id": {
                    "type": "string",
                    "description": "Gmail message ID (for read action)"
                },
                "to": {
                    "type": "string",
                    "description": "Recipient email address (for send action)"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject (for send action)"
                },
                "body": {
                    "type": "string",
                    "description": "Email body text (for send action)"
                },
                "max_results": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results to return (for search)"
                }
            },
            "required": ["action"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Gmail tool with given arguments."""
        action = args.get("action")

        try:
            # Check if mcp-gmail is installed
            try:
                from mcp_gmail import GmailClient
            except ImportError:
                return {
                    "error": "Gmail integration not set up. Please install mcp-gmail: pip install mcp-gmail",
                    "setup_required": True
                }

            # Check for credentials
            credentials_path = GmailTool.CREDENTIALS_DIR / "gmail_credentials.json"
            if not credentials_path.exists():
                return {
                    "error": f"Gmail credentials not found. Please add credentials.json to {GmailTool.CREDENTIALS_DIR}",
                    "setup_required": True,
                    "instructions": "1. Go to Google Cloud Console\n2. Create OAuth 2.0 credentials\n3. Download and save as gmail_credentials.json"
                }

            # Initialize Gmail client
            client = GmailClient(credentials_path=str(credentials_path))

            # Execute action
            if action == "search":
                query = args.get("query", "")
                max_results = args.get("max_results", 10)

                messages = await client.list_messages(query=query, max_results=max_results)

                return {
                    "action": "search",
                    "query": query,
                    "count": len(messages),
                    "messages": [
                        {
                            "id": msg.get("id"),
                            "thread_id": msg.get("threadId"),
                            "snippet": msg.get("snippet", ""),
                        }
                        for msg in messages
                    ]
                }

            elif action == "read":
                message_id = args.get("message_id")
                if not message_id:
                    return {"error": "message_id is required for read action"}

                message = await client.get_message(message_id)

                return {
                    "action": "read",
                    "message_id": message_id,
                    "subject": message.get("subject"),
                    "from": message.get("from"),
                    "to": message.get("to"),
                    "date": message.get("date"),
                    "body": message.get("body"),
                    "snippet": message.get("snippet")
                }

            elif action == "send":
                to = args.get("to")
                subject = args.get("subject", "")
                body = args.get("body", "")

                if not to:
                    return {"error": "to address is required for send action"}

                result = await client.send_message(
                    to=to,
                    subject=subject,
                    message_text=body
                )

                return {
                    "action": "send",
                    "success": True,
                    "message_id": result.get("id"),
                    "to": to,
                    "subject": subject
                }

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            logger.error(f"Gmail tool error: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def is_configured() -> bool:
        """Check if Gmail credentials are configured."""
        credentials_path = GmailTool.CREDENTIALS_DIR / "gmail_credentials.json"
        return credentials_path.exists()

    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        """Get setup instructions for Gmail integration."""
        return {
            "tool": "gmail",
            "requires_oauth": True,
            "steps": [
                {
                    "step": 1,
                    "title": "Create Google Cloud Project",
                    "description": "Go to Google Cloud Console",
                    "url": "https://console.cloud.google.com",
                    "action": "Create a new project or select existing"
                },
                {
                    "step": 2,
                    "title": "Enable Gmail API",
                    "description": "Enable the Gmail API for your project",
                    "action": "Go to APIs & Services > Library, search 'Gmail API', click Enable"
                },
                {
                    "step": 3,
                    "title": "Create OAuth Credentials",
                    "description": "Create OAuth 2.0 Desktop credentials",
                    "action": "Go to APIs & Services > Credentials > Create Credentials > OAuth client ID > Desktop app"
                },
                {
                    "step": 4,
                    "title": "Download Credentials",
                    "description": "Download the credentials JSON file",
                    "action": "Click the download icon next to your OAuth client"
                },
                {
                    "step": 5,
                    "title": "Upload to Drakyn",
                    "description": "Upload the credentials file using the chat interface",
                    "action": "I can help you upload it - just paste the contents or use the upload button"
                }
            ],
            "quick_summary": "To use Gmail, I need OAuth credentials from Google Cloud Console. I'll guide you through the setup step-by-step."
        }
