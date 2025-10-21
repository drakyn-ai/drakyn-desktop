"""
Learning system for proactive agent.

Asks questions to learn about the user and updates user context.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class LearningSystem:
    """
    Manages proactive learning about the user.
    Asks questions and updates user context based on answers.
    """

    def __init__(
        self,
        mcp_url: str = "http://localhost:8001",
        inference_url: str = "http://localhost:8000",
        electron_ipc_url: str = "http://localhost:9999",
        max_questions_per_day: int = 3
    ):
        """
        Initialize learning system.

        Args:
            mcp_url: URL of MCP server
            inference_url: URL of inference server
            electron_ipc_url: URL for Electron IPC
            max_questions_per_day: Maximum questions to ask per day
        """
        self.mcp_url = mcp_url
        self.inference_url = inference_url
        self.electron_ipc_url = electron_ipc_url
        self.max_questions_per_day = max_questions_per_day

        # User data directory
        self.user_dir = Path.home() / ".drakyn"
        self.user_dir.mkdir(exist_ok=True)
        self.context_file = self.user_dir / "user_context.txt"
        self.questions_log = self.user_dir / "questions_asked.txt"

    async def should_ask_question(self) -> bool:
        """
        Determine if we should ask a learning question.

        Returns:
            True if we should ask a question, False otherwise
        """
        # Check if we've reached daily limit
        questions_today = self._count_questions_today()
        if questions_today >= self.max_questions_per_day:
            logger.info(f"Already asked {questions_today} questions today (max: {self.max_questions_per_day})")
            return False

        # Read user context to check completeness
        user_context = await self._read_user_context()

        # Ask agent if it needs more information
        prompt = f"""You are Drakyn, a proactive AI assistant.

What you currently know about the user:
{user_context}

Looking at what you know, is there important information missing that would help you be more helpful?
Consider: work schedule, family, preferences, important contacts, daily routines, goals

If you'd like to ask 1 question to learn more, respond with:
QUESTION: [Your question]

If you have enough context for now, respond with:
NO_QUESTION

Remember: Don't ask too many questions. Only ask if the information would be truly valuable.
"""

        try:
            response = await self._call_agent(prompt)

            # Check if agent wants to ask a question
            if "QUESTION:" in response:
                return True
            else:
                logger.info("Agent decided it has enough context")
                return False

        except Exception as e:
            logger.error(f"Failed to check if should ask question: {str(e)}")
            return False

    async def generate_question(self) -> Optional[str]:
        """
        Generate a learning question for the user.

        Returns:
            Question string or None if no question
        """
        user_context = await self._read_user_context()

        prompt = f"""You are Drakyn, a proactive AI assistant.

What you currently know about the user:
{user_context}

Generate ONE helpful question to learn more about the user's life, preferences, or routines.
The question should be conversational and friendly, not interrogative.

Format:
QUESTION: [Your question]

Examples of good questions:
- "What time do you usually start your workday?"
- "Do you have any children I should know about?"
- "What are your main priorities this week?"
- "Are there any regular appointments or commitments you have?"
"""

        try:
            response = await self._call_agent(prompt)

            # Extract question
            if "QUESTION:" in response:
                lines = response.split("\n")
                for line in lines:
                    if line.strip().startswith("QUESTION:"):
                        question = line.replace("QUESTION:", "").strip()
                        return question

            return None

        except Exception as e:
            logger.error(f"Failed to generate question: {str(e)}")
            return None

    async def ask_question(self, question: str):
        """
        Send learning question to user via notification.

        Args:
            question: Question to ask
        """
        try:
            # Send to Electron as a special "learning question" notification
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{self.electron_ipc_url}/notify",
                    json={
                        "title": "Drakyn wants to learn",
                        "body": question,
                        "data": {
                            "type": "learning_question",
                            "question": question
                        }
                    }
                )

            # Log the question
            self._log_question(question)
            logger.info(f"Asked learning question: {question}")

        except Exception as e:
            logger.error(f"Failed to ask question: {str(e)}")

    async def process_answer(self, question: str, answer: str):
        """
        Process user's answer and update context.

        Args:
            question: Question that was asked
            answer: User's answer
        """
        try:
            # Read current user context
            user_context = await self._read_user_context()

            # Ask agent to update context with new information
            prompt = f"""You are Drakyn, a proactive AI assistant.

You asked the user: "{question}"
They responded: "{answer}"

Current user context:
{user_context}

Update the user context file to include this new information.
Integrate it naturally into the existing context, organizing it appropriately.

Use the user_context tool with action='update' to rewrite the file.
Include all existing information plus the new information.
"""

            # Call agent with tools enabled
            # Agent will use user_context tool to update the file
            await self._call_agent_with_tools(prompt)

            logger.info(f"Updated user context based on answer to: {question}")

        except Exception as e:
            logger.error(f"Failed to process answer: {str(e)}")

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

    async def _call_agent(self, prompt: str) -> str:
        """Call agent LLM without tools"""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.inference_url}/v1/chat/completions",
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "stream": False
                    }
                )
                response.raise_for_status()
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return ""

        except Exception as e:
            logger.error(f"Failed to call agent: {str(e)}")
            raise

    async def _call_agent_with_tools(self, prompt: str):
        """Call agent with tools enabled (for updating context)"""
        try:
            # Use the agent chat endpoint which has tool support
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.inference_url}/v1/agent/chat",
                    json={
                        "message": prompt,
                        "stream": False
                    }
                )
                response.raise_for_status()
                # Agent will call user_context tool to update the file
                logger.info("Agent called with tools to update context")

        except Exception as e:
            logger.error(f"Failed to call agent with tools: {str(e)}")
            raise

    def _count_questions_today(self) -> int:
        """Count how many questions asked today"""
        try:
            if not self.questions_log.exists():
                return 0

            today = datetime.now().date()
            count = 0

            with open(self.questions_log, "r") as f:
                for line in f:
                    if line.strip():
                        # Parse timestamp
                        try:
                            timestamp_str = line.split("]")[0].replace("[", "")
                            timestamp = datetime.fromisoformat(timestamp_str)
                            if timestamp.date() == today:
                                count += 1
                        except Exception:
                            continue

            return count

        except Exception as e:
            logger.warning(f"Failed to count questions: {str(e)}")
            return 0

    def _log_question(self, question: str):
        """Log question to file"""
        try:
            with open(self.questions_log, "a") as f:
                timestamp = datetime.now().isoformat()
                f.write(f"[{timestamp}] {question}\n")
        except Exception as e:
            logger.warning(f"Failed to log question: {str(e)}")
