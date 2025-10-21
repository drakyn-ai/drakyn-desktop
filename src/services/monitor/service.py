"""
Background monitoring service for proactive agent.

Runs periodically to:
1. Gather context snapshots (emails, calendar, system state)
2. Analyze context using LLM
3. Generate proactive suggestions
4. Send notifications to user
"""
import asyncio
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import httpx
from notifications import NotificationManager
from learning import LearningSystem

logger = logging.getLogger(__name__)


class BackgroundMonitor:
    """
    Monitors user context and triggers proactive suggestions.
    Runs as a continuous background service.
    """

    def __init__(
        self,
        mcp_url: str = "http://localhost:8001",
        inference_url: str = "http://localhost:8000",
        electron_ipc_url: str = "http://localhost:9999",
        check_interval_minutes: int = 30
    ):
        """
        Initialize background monitor.

        Args:
            mcp_url: URL of MCP server for tool execution
            inference_url: URL of inference server for agent chat
            electron_ipc_url: URL for Electron IPC server
            check_interval_minutes: How often to check context (default: 30 minutes)
        """
        self.mcp_url = mcp_url
        self.inference_url = inference_url
        self.check_interval_minutes = check_interval_minutes

        # User data directory
        self.user_dir = Path.home() / ".drakyn"
        self.user_dir.mkdir(exist_ok=True)

        # Context files
        self.context_file = self.user_dir / "user_context.txt"
        self.suggestion_history_file = self.user_dir / "suggestion_history.txt"

        # Notification manager
        self.notifier = NotificationManager(electron_ipc_url)

        # Learning system
        self.learner = LearningSystem(mcp_url, inference_url, electron_ipc_url)

        # Learning check counter (ask questions less frequently than suggestions)
        self.check_count = 0

        logger.info(f"Background monitor initialized with {check_interval_minutes}min interval")

    async def run_forever(self):
        """
        Main monitoring loop - runs continuously.
        """
        logger.info("Starting background monitor service...")

        while True:
            try:
                # Read user preferences from context file
                preferences = await self._read_user_preferences()

                # Check if monitoring is enabled
                if not preferences.get("enabled", True):
                    logger.info("Proactive monitoring is disabled. Sleeping...")
                    await asyncio.sleep(60 * 5)  # Check every 5 minutes if it gets re-enabled
                    continue

                # Check if we're in quiet hours
                if self._is_quiet_hours(preferences):
                    logger.info("Currently in quiet hours. Skipping this check.")
                    await asyncio.sleep(60 * self.check_interval_minutes)
                    continue

                logger.info("=== Starting proactive check ===")

                # Gather current context
                context_snapshot = await self.gather_context()
                logger.info(f"Gathered context snapshot ({len(context_snapshot)} chars)")

                # Analyze context and get suggestions
                suggestions = await self.analyze_context(context_snapshot)

                if suggestions:
                    logger.info(f"Generated {len(suggestions)} suggestions")
                    await self._notify_suggestions(suggestions)
                else:
                    logger.info("No suggestions generated (agent decided nothing helpful right now)")

                # Every 3rd check, consider asking a learning question
                self.check_count += 1
                if self.check_count % 3 == 0:
                    logger.info("Checking if should ask learning question...")
                    try:
                        if await self.learner.should_ask_question():
                            question = await self.learner.generate_question()
                            if question:
                                await self.learner.ask_question(question)
                                logger.info(f"Asked learning question: {question}")
                    except Exception as e:
                        logger.error(f"Failed to ask learning question: {str(e)}")

                logger.info("=== Proactive check complete ===")

            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}", exc_info=True)

            # Sleep until next check
            sleep_seconds = 60 * self.check_interval_minutes
            logger.info(f"Sleeping for {self.check_interval_minutes} minutes...")
            await asyncio.sleep(sleep_seconds)

    async def gather_context(self) -> str:
        """
        Gather current context snapshot from various sources.

        Returns:
            Plain text context snapshot to be analyzed by agent
        """
        lines = []
        lines.append(f"Current Time: {datetime.now().strftime('%I:%M %p, %A %B %d, %Y')}")
        lines.append("")

        # Check emails via MCP Gmail tool
        try:
            emails = await self._check_emails()
            if emails and len(emails) > 0:
                lines.append("Recent Emails:")
                for email in emails[:5]:  # Show up to 5 most recent
                    lines.append(f"  - From {email.get('from', 'unknown')}: {email.get('subject', 'No subject')}")
                lines.append("")
        except Exception as e:
            logger.warning(f"Failed to check emails: {str(e)}")

        # Check calendar (to be implemented when calendar tool exists)
        # For now, skip calendar checks
        # try:
        #     events = await self._check_calendar()
        #     if events:
        #         lines.append("Upcoming Events (next 24 hours):")
        #         for event in events:
        #             lines.append(f"  - {event['time']}: {event['title']}")
        #         lines.append("")
        # except Exception as e:
        #     logger.warning(f"Failed to check calendar: {str(e)}")

        # Check system state
        try:
            system_info = await self._check_system_state()
            lines.append("System State:")
            if system_info.get("battery_percent"):
                lines.append(f"  - Battery: {system_info['battery_percent']}%")
            lines.append("")
        except Exception as e:
            logger.warning(f"Failed to check system state: {str(e)}")

        return "\n".join(lines)

    async def analyze_context(self, context_snapshot: str) -> List[Dict[str, Any]]:
        """
        Analyze context using agent's LLM to generate suggestions.

        Args:
            context_snapshot: Current context gathered from various sources

        Returns:
            List of suggestion dictionaries
        """
        # Read user context
        user_context = await self._read_user_context()

        # Build prompt for agent
        prompt = f"""You are Drakyn, a proactive AI assistant.

What you know about the user:
{user_context}

Current situation:
{context_snapshot}

Based on what you know about the user and their current situation:
1. Are there any helpful actions you could take right now?
2. Consider: upcoming events, important emails, battery level, time of day
3. Respect the user's preferences about notification frequency and style

If you have 1-3 helpful suggestions, respond with them in this format:
SUGGESTIONS:
- [Brief description of action]: [Why this would be helpful]

If nothing urgent or helpful right now, respond with:
NO_SUGGESTIONS

Remember: Better to stay quiet than be annoying. Only suggest truly helpful things.
"""

        try:
            # Call agent via inference server
            response = await self._call_agent(prompt)

            # Parse suggestions from response
            suggestions = self._parse_suggestions(response)

            return suggestions

        except Exception as e:
            logger.error(f"Failed to analyze context: {str(e)}")
            return []

    async def _check_emails(self) -> List[Dict[str, Any]]:
        """Check for recent unread emails via MCP Gmail tool"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.mcp_url}/execute",
                    json={
                        "tool": "gmail",
                        "arguments": {
                            "action": "search",
                            "query": "is:unread",
                            "max_results": 5
                        }
                    }
                )
                response.raise_for_status()
                result = response.json()

                if result.get("error"):
                    logger.warning(f"Gmail tool returned error: {result['error']}")
                    return []

                # Extract emails from result
                emails = result.get("result", {}).get("emails", [])
                return emails

        except Exception as e:
            logger.warning(f"Failed to check emails: {str(e)}")
            return []

    async def _check_system_state(self) -> Dict[str, Any]:
        """Check system state (battery, etc.)"""
        info = {}

        try:
            # Check battery level (Linux)
            battery_path = Path("/sys/class/power_supply/BAT0/capacity")
            if battery_path.exists():
                capacity = battery_path.read_text().strip()
                info["battery_percent"] = int(capacity)
        except Exception as e:
            logger.debug(f"Could not read battery level: {str(e)}")

        return info

    async def _call_agent(self, prompt: str) -> str:
        """
        Call agent's LLM via inference server.

        Args:
            prompt: Prompt to send to agent

        Returns:
            Agent's response text
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Use the agent chat endpoint (non-streaming for simplicity)
                response = await client.post(
                    f"{self.inference_url}/v1/chat/completions",
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()

                # Extract response content
                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.error(f"Unexpected response format: {result}")
                    return ""

        except Exception as e:
            logger.error(f"Failed to call agent: {str(e)}")
            raise

    def _parse_suggestions(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse suggestions from agent's response.

        Args:
            response: Agent's text response

        Returns:
            List of suggestion dictionaries
        """
        suggestions = []

        # Check if agent said no suggestions
        if "NO_SUGGESTIONS" in response:
            return []

        # Look for SUGGESTIONS: section
        if "SUGGESTIONS:" not in response:
            return []

        # Extract suggestions (each line starting with -)
        in_suggestions = False
        for line in response.split("\n"):
            line = line.strip()

            if line == "SUGGESTIONS:":
                in_suggestions = True
                continue

            if in_suggestions and line.startswith("-"):
                # Parse suggestion line
                suggestion_text = line[1:].strip()  # Remove leading "-"

                # Try to split into action and reasoning
                if ":" in suggestion_text:
                    action, reasoning = suggestion_text.split(":", 1)
                    suggestions.append({
                        "action": action.strip(),
                        "reasoning": reasoning.strip(),
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    suggestions.append({
                        "action": suggestion_text,
                        "reasoning": "",
                        "timestamp": datetime.now().isoformat()
                    })

        return suggestions

    async def _read_user_context(self) -> str:
        """Read user context file"""
        try:
            if self.context_file.exists():
                return self.context_file.read_text()
            else:
                return "No user context available yet."
        except Exception as e:
            logger.error(f"Failed to read user context: {str(e)}")
            return "Error reading user context."

    async def _read_user_preferences(self) -> Dict[str, Any]:
        """
        Read user preferences from context file.

        Returns:
            Dictionary with preferences like enabled, quiet_hours, etc.
        """
        preferences = {
            "enabled": True,
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "07:00"
        }

        try:
            context = await self._read_user_context()

            # Parse quiet hours from context (using regex for HH:MM - HH:MM pattern)
            import re
            for line in context.split("\n"):
                if "quiet hours:" in line.lower():
                    # Extract HH:MM - HH:MM pattern
                    time_pattern = r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})'
                    match = re.search(time_pattern, line)
                    if match:
                        preferences["quiet_hours_start"] = match.group(1)
                        preferences["quiet_hours_end"] = match.group(2)

                if "proactive" in line.lower() and "disabled" in line.lower():
                    preferences["enabled"] = False

        except Exception as e:
            logger.warning(f"Failed to parse preferences: {str(e)}")

        return preferences

    def _is_quiet_hours(self, preferences: Dict[str, Any]) -> bool:
        """Check if current time is in quiet hours"""
        try:
            now = datetime.now()
            current_time = now.strftime("%H:%M")

            start = preferences.get("quiet_hours_start", "22:00")
            end = preferences.get("quiet_hours_end", "07:00")

            # Handle overnight quiet hours (e.g., 22:00 - 07:00)
            if start > end:
                return current_time >= start or current_time <= end
            else:
                return start <= current_time <= end

        except Exception as e:
            logger.warning(f"Failed to check quiet hours: {str(e)}")
            return False

    async def _notify_suggestions(self, suggestions: List[Dict[str, Any]]):
        """
        Send suggestions to user via notification manager.

        Args:
            suggestions: List of suggestions to notify
        """
        # Send via notification manager (system notifications + in-app)
        await self.notifier.send_suggestions(suggestions)

        # Also append to suggestion history file
        try:
            with open(self.suggestion_history_file, "a") as f:
                for suggestion in suggestions:
                    f.write(f"\n[{suggestion['timestamp']}] SUGGESTED: {suggestion['action']}\n")
                    if suggestion.get('reasoning'):
                        f.write(f"  REASONING: {suggestion['reasoning']}\n")
                    f.write(f"  STATUS: pending\n")
        except Exception as e:
            logger.warning(f"Failed to write suggestion history: {str(e)}")


async def main():
    """Main entry point for running the monitor service."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create and run monitor
    monitor = BackgroundMonitor(
        check_interval_minutes=int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
    )

    await monitor.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
