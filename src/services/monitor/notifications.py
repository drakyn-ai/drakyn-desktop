"""
Notification manager for proactive agent suggestions.

Sends suggestions to the user via:
1. System notifications (via Electron IPC)
2. In-app suggestion panel (via WebSocket)
"""
import asyncio
import logging
from typing import Dict, Any, List
import httpx
import json

logger = logging.getLogger(__name__)


class NotificationManager:
    """
    Manages delivery of proactive suggestions to user.
    """

    def __init__(self, electron_ipc_url: str = "http://localhost:9999"):
        """
        Initialize notification manager.

        Args:
            electron_ipc_url: URL for communicating with Electron main process
        """
        self.electron_ipc_url = electron_ipc_url

    async def send_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        Send suggestions to user via available channels.

        Args:
            suggestions: List of suggestion dictionaries
        """
        if not suggestions:
            return

        logger.info(f"Sending {len(suggestions)} suggestions to user")

        # Try system notifications first (via Electron)
        try:
            await self._send_system_notifications(suggestions)
        except Exception as e:
            logger.warning(f"Failed to send system notifications: {str(e)}")
            # Fall back to just logging
            self._log_suggestions(suggestions)

    async def _send_system_notifications(self, suggestions: List[Dict[str, Any]]):
        """
        Send system notifications via Electron IPC.

        Args:
            suggestions: List of suggestions
        """
        try:
            # Send to Electron main process
            async with httpx.AsyncClient(timeout=5.0) as client:
                for suggestion in suggestions:
                    await client.post(
                        f"{self.electron_ipc_url}/notify",
                        json={
                            "title": "Drakyn Suggestion",
                            "body": suggestion["action"],
                            "data": suggestion
                        }
                    )
                    # Small delay between notifications
                    await asyncio.sleep(0.5)

            logger.info(f"Sent {len(suggestions)} system notifications")

        except httpx.ConnectError:
            logger.debug("Electron IPC server not available, using fallback")
            raise
        except Exception as e:
            logger.error(f"Error sending system notifications: {str(e)}")
            raise

    def _log_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        Fallback: log suggestions to console.

        Args:
            suggestions: List of suggestions
        """
        logger.info("=== SUGGESTIONS ===")
        for i, suggestion in enumerate(suggestions, 1):
            logger.info(f"{i}. {suggestion['action']}")
            if suggestion.get('reasoning'):
                logger.info(f"   Why: {suggestion['reasoning']}")

    async def record_user_action(
        self,
        suggestion: Dict[str, Any],
        action: str,
        feedback: str = ""
    ):
        """
        Record user's response to a suggestion.

        Args:
            suggestion: The suggestion shown to user
            action: User action ("accepted", "dismissed", "ignored")
            feedback: Optional user feedback
        """
        from pathlib import Path
        from datetime import datetime

        try:
            history_file = Path.home() / ".drakyn" / "suggestion_history.txt"

            with open(history_file, "a") as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"\n[{timestamp}] SUGGESTED: {suggestion['action']}\n")
                if suggestion.get('reasoning'):
                    f.write(f"  REASONING: {suggestion['reasoning']}\n")
                f.write(f"  USER ACTION: {action}\n")
                if feedback:
                    f.write(f"  FEEDBACK: {feedback}\n")

            logger.info(f"Recorded user action: {action}")

        except Exception as e:
            logger.error(f"Failed to record user action: {str(e)}")
