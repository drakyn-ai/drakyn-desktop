"""
Gmail MCP Tool - Provides email reading and sending capabilities via Gmail API.
Uses browser-based OAuth flow for easy user authentication.
"""
import logging
from typing import Dict, Any, List, Optional
import os
import json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import base64
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

# Gmail API scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]

# Drakyn's OAuth credentials (Desktop application)
# NOTE: These are publicly visible in a desktop app - this is normal and expected
# Security comes from the redirect URI and user consent, not secret client credentials

# Try to load from environment variables first (more secure)
# Fall back to hardcoded values for development
def get_oauth_config():
    """Get OAuth configuration from environment or defaults."""
    client_id = os.getenv("GOOGLE_CLIENT_ID", "YOUR_CLIENT_ID.apps.googleusercontent.com")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }

OAUTH_CLIENT_CONFIG = get_oauth_config()


class GmailTool:
    """Tool for Gmail operations with browser-based OAuth."""

    name = "gmail"
    description = "Search, read, and send Gmail messages. Supports searching by query, reading email content, and sending new emails."

    # Token storage path (user's tokens, not app credentials)
    TOKENS_DIR = Path(__file__).parent.parent / "tokens"
    TOKEN_FILE = TOKENS_DIR / "gmail_token.json"

    @staticmethod
    def _get_credentials() -> Optional[Credentials]:
        """
        Get valid Gmail API credentials.
        Uses browser-based OAuth flow if needed.

        Returns:
            Valid credentials or None if authentication fails
        """
        creds = None

        # Create tokens directory if it doesn't exist
        GmailTool.TOKENS_DIR.mkdir(parents=True, exist_ok=True)

        # Load existing token if available
        if GmailTool.TOKEN_FILE.exists():
            try:
                creds = Credentials.from_authorized_user_file(str(GmailTool.TOKEN_FILE), SCOPES)
                logger.info("Loaded existing Gmail credentials")
            except Exception as e:
                logger.warning(f"Failed to load existing credentials: {e}")
                creds = None

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    logger.info("Refreshing expired Gmail credentials")
                    creds.refresh(Request())
                    logger.info("Successfully refreshed credentials")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    creds = None

            if not creds:
                # Generate OAuth URL that user needs to visit
                logger.info("Generating OAuth authorization URL")
                try:
                    flow = InstalledAppFlow.from_client_config(
                        OAUTH_CLIENT_CONFIG,
                        SCOPES
                    )

                    # Use a fixed port for OAuth redirect
                    port = 8080
                    flow.redirect_uri = f'http://localhost:{port}'
                    auth_url, _ = flow.authorization_url(prompt='consent')

                    logger.info("=" * 80)
                    logger.info("OAUTH URL GENERATED")
                    logger.info("=" * 80)
                    logger.info(f"URL: {auth_url}")
                    logger.info(f"Port: {port}")
                    logger.info("=" * 80)

                    # Store the port for later use (we don't need to persist the full flow)
                    import json
                    flow_state = {
                        "port": port
                    }

                    # Save flow state to temp file
                    flow_file = GmailTool.TOKENS_DIR / "oauth_flow_state.json"
                    GmailTool.TOKENS_DIR.mkdir(parents=True, exist_ok=True)
                    with open(flow_file, 'w') as f:
                        json.dump(flow_state, f)

                    # Return None to indicate auth needed - URL will be in error response
                    return {
                        "auth_needed": True,
                        "auth_url": auth_url,
                        "port": port,
                        "message": f"Please visit the URL above in your browser and sign in. After authorization, you'll be redirected to localhost:{port}. Copy the FULL redirect URL and submit it with the submit_url action."
                    }

                except Exception as e:
                    logger.error(f"Failed to generate OAuth URL: {e}")
                    logger.exception("Full error:")
                    return None

            # Save the credentials for future use
            if creds:
                try:
                    with open(GmailTool.TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"Saved credentials to {GmailTool.TOKEN_FILE}")
                except Exception as e:
                    logger.error(f"Failed to save credentials: {e}")

        return creds

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return the JSON schema for Gmail tool parameters."""
        return {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["search", "read", "send", "authenticate", "submit_code", "submit_url"],
                    "description": "Action to perform: search for emails, read a specific email, send a new email, authenticate with Google, submit authorization code, or submit redirect URL"
                },
                "code": {
                    "type": "string",
                    "description": "Authorization code from Google (for submit_code action)"
                },
                "url": {
                    "type": "string",
                    "description": "Full redirect URL from browser (for submit_url action)"
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
            # Handle submit_url action
            if action == "submit_url":
                redirect_url = args.get("url")
                if not redirect_url:
                    return {"error": "Redirect URL is required for submit_url action"}

                logger.info(f"Submitting redirect URL: {redirect_url}")
                try:
                    # Load flow state
                    import json
                    from urllib.parse import urlparse, parse_qs

                    flow_file = GmailTool.TOKENS_DIR / "oauth_flow_state.json"
                    if not flow_file.exists():
                        return {"error": "OAuth flow state not found. Please call authenticate action first."}

                    with open(flow_file, 'r') as f:
                        flow_state = json.load(f)

                    port = flow_state.get("port")

                    # Parse the authorization code from URL
                    parsed = urlparse(redirect_url)
                    params = parse_qs(parsed.query)
                    code = params.get('code', [None])[0]

                    if not code:
                        return {"error": "No authorization code found in URL"}

                    # Create new flow and fetch token
                    flow = InstalledAppFlow.from_client_config(
                        OAUTH_CLIENT_CONFIG,
                        SCOPES
                    )
                    flow.redirect_uri = f'http://localhost:{port}'
                    flow.fetch_token(code=code)
                    creds = flow.credentials

                    # Save the credentials
                    GmailTool.TOKENS_DIR.mkdir(parents=True, exist_ok=True)
                    with open(GmailTool.TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"Saved credentials to {GmailTool.TOKEN_FILE}")

                    # Clean up flow state
                    flow_file.unlink()

                    return {
                        "action": "submit_url",
                        "success": True,
                        "message": "Successfully authenticated with Gmail! You can now access your emails."
                    }
                except Exception as e:
                    logger.error(f"Failed to process redirect URL: {e}")
                    logger.exception("Full error:")
                    return {
                        "action": "submit_url",
                        "success": False,
                        "error": f"Failed to authenticate: {str(e)}"
                    }

            # Handle submit_code action (legacy)
            if action == "submit_code":
                code = args.get("code")
                if not code:
                    return {"error": "Authorization code is required for submit_code action"}

                logger.info("Submitting authorization code")
                try:
                    flow = InstalledAppFlow.from_client_config(
                        OAUTH_CLIENT_CONFIG,
                        SCOPES
                    )
                    flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'
                    flow.fetch_token(code=code)
                    creds = flow.credentials

                    # Save the credentials
                    GmailTool.TOKENS_DIR.mkdir(parents=True, exist_ok=True)
                    with open(GmailTool.TOKEN_FILE, 'w') as token:
                        token.write(creds.to_json())
                    logger.info(f"Saved credentials to {GmailTool.TOKEN_FILE}")

                    return {
                        "action": "submit_code",
                        "success": True,
                        "message": "Successfully authenticated with Gmail! You can now access your emails."
                    }
                except Exception as e:
                    logger.error(f"Failed to exchange code for token: {e}")
                    return {
                        "action": "submit_code",
                        "success": False,
                        "error": f"Failed to authenticate: {str(e)}"
                    }

            # Handle authentication action
            if action == "authenticate":
                logger.info("Explicit authentication requested")
                creds = GmailTool._get_credentials()
                if isinstance(creds, dict) and creds.get("auth_needed"):
                    # Return the auth URL
                    return creds
                elif creds:
                    return {
                        "action": "authenticate",
                        "success": True,
                        "message": "Successfully authenticated with Gmail! You can now access your emails."
                    }
                else:
                    return {
                        "action": "authenticate",
                        "success": False,
                        "error": "Authentication failed. Please check the logs."
                    }

            # Get credentials (will trigger OAuth flow if needed)
            creds = GmailTool._get_credentials()

            if not creds:
                return {
                    "error": "Unable to authenticate with Gmail. Please try again.",
                    "setup_required": True,
                    "instructions": "I'll open your browser to sign in with Google. Click 'Allow' to grant access to your Gmail.",
                    "type": "authentication_required"
                }

            # Build Gmail service
            service = build('gmail', 'v1', credentials=creds)

            # Execute action
            if action == "search":
                query = args.get("query", "")
                max_results = args.get("max_results", 10)

                logger.info(f"Searching Gmail with query: {query}")
                results = service.users().messages().list(
                    userId='me',
                    q=query,
                    maxResults=max_results
                ).execute()

                messages = results.get('messages', [])

                # Get details for each message
                detailed_messages = []
                for msg in messages:
                    msg_detail = service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='metadata',
                        metadataHeaders=['From', 'Subject', 'Date']
                    ).execute()

                    headers = {h['name']: h['value'] for h in msg_detail.get('payload', {}).get('headers', [])}

                    detailed_messages.append({
                        "id": msg['id'],
                        "thread_id": msg.get('threadId'),
                        "snippet": msg_detail.get('snippet', ''),
                        "from": headers.get('From', 'Unknown'),
                        "subject": headers.get('Subject', '(No subject)'),
                        "date": headers.get('Date', 'Unknown')
                    })

                return {
                    "action": "search",
                    "query": query,
                    "count": len(detailed_messages),
                    "messages": detailed_messages
                }

            elif action == "read":
                message_id = args.get("message_id")
                if not message_id:
                    return {"error": "message_id is required for read action"}

                logger.info(f"Reading email: {message_id}")
                message = service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()

                # Parse headers
                headers = {h['name']: h['value'] for h in message.get('payload', {}).get('headers', [])}

                # Extract body
                def get_body(payload):
                    """Recursively extract email body."""
                    if 'body' in payload and 'data' in payload['body']:
                        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

                    if 'parts' in payload:
                        for part in payload['parts']:
                            if part.get('mimeType') == 'text/plain':
                                if 'data' in part.get('body', {}):
                                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            body = get_body(part)
                            if body:
                                return body
                    return None

                body = get_body(message.get('payload', {}))

                return {
                    "action": "read",
                    "message_id": message_id,
                    "subject": headers.get('Subject', '(No subject)'),
                    "from": headers.get('From', 'Unknown'),
                    "to": headers.get('To', 'Unknown'),
                    "date": headers.get('Date', 'Unknown'),
                    "body": body or message.get('snippet', ''),
                    "snippet": message.get('snippet', '')
                }

            elif action == "send":
                to = args.get("to")
                subject = args.get("subject", "")
                body = args.get("body", "")

                if not to:
                    return {"error": "to address is required for send action"}

                logger.info(f"Sending email to: {to}")

                # Create message
                message = MIMEText(body)
                message['to'] = to
                message['subject'] = subject

                # Encode message
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

                # Send message
                result = service.users().messages().send(
                    userId='me',
                    body={'raw': raw}
                ).execute()

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
            logger.exception("Full traceback:")

            # Check if this is an auth error
            if "credentials" in str(e).lower() or "auth" in str(e).lower():
                # Delete the token file so next attempt will re-authenticate
                if GmailTool.TOKEN_FILE.exists():
                    GmailTool.TOKEN_FILE.unlink()
                    logger.info("Deleted invalid token file")

                return {
                    "error": "Authentication failed. Please try again to sign in with Google.",
                    "setup_required": True,
                    "type": "authentication_error"
                }

            return {"error": str(e)}

    @staticmethod
    def is_configured() -> bool:
        """Check if Gmail credentials are configured."""
        return GmailTool.TOKEN_FILE.exists()

    @staticmethod
    def get_setup_instructions() -> Dict[str, Any]:
        """Get setup instructions for Gmail integration."""
        return {
            "tool": "gmail",
            "requires_oauth": True,
            "browser_based": True,
            "steps": [
                {
                    "step": 1,
                    "title": "Sign in with Google",
                    "description": "I'll open your browser to Google's sign-in page",
                    "action": "Click 'Allow' when prompted to grant Gmail access"
                },
                {
                    "step": 2,
                    "title": "Grant Permissions",
                    "description": "Allow Drakyn to read and send emails on your behalf",
                    "action": "Review the permissions and click 'Allow'"
                },
                {
                    "step": 3,
                    "title": "Done!",
                    "description": "You'll be redirected back to the app",
                    "action": "You can now access your Gmail through me"
                }
            ],
            "quick_summary": "I'll open your browser so you can sign in with Google. Just click 'Allow' and you're all set!",
            "estimated_time": "30 seconds"
        }
