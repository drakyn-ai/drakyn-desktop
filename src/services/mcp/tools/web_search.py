"""
Web Search MCP Tool - Provides Google Custom Search capabilities.
Uses Google Custom Search API with user's Google credentials.
"""
import logging
from typing import Dict, Any, List
import os
import requests

logger = logging.getLogger(__name__)

class WebSearchTool:
    """Tool for searching the web using Google Custom Search API."""

    name = "web_search"
    description = "Search the web using Google Custom Search API. Useful for finding information, MCP servers, or any web content."

    # Google Custom Search API endpoint
    SEARCH_URL = "https://www.googleapis.com/customsearch/v1"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Return the tool schema for the agent."""
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to execute"
                },
                "num_results": {
                    "type": "integer",
                    "description": "Number of results to return (max 10)",
                    "default": 5
                },
                "site_restrict": {
                    "type": "string",
                    "description": "Optional: Restrict search to specific site (e.g., 'github.com')"
                }
            },
            "required": ["query"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute web search with given query."""
        query = args.get("query")
        num_results = min(args.get("num_results", 5), 10)
        site_restrict = args.get("site_restrict")

        if not query:
            return {"error": "Search query is required"}

        try:
            # Get API key and Search Engine ID from environment
            api_key = os.getenv("GOOGLE_CUSTOM_SEARCH_API_KEY")
            search_engine_id = os.getenv("GOOGLE_CUSTOM_SEARCH_ENGINE_ID")

            if not api_key or not search_engine_id:
                return {
                    "setup_required": True,
                    "error": "Google Custom Search API not configured",
                    "instructions": [
                        "1. Go to https://console.cloud.google.com/apis/library",
                        "2. Enable the 'Custom Search API'",
                        "3. Go to https://programmablesearchengine.google.com/",
                        "4. Create a new search engine (or use existing one)",
                        "5. Get your Search Engine ID",
                        "6. Get your API key from Google Cloud Console",
                        "7. Add GOOGLE_CUSTOM_SEARCH_API_KEY and GOOGLE_CUSTOM_SEARCH_ENGINE_ID to your .env file"
                    ]
                }

            # Build search query
            search_query = query
            if site_restrict:
                search_query = f"site:{site_restrict} {query}"

            # Call Google Custom Search API
            params = {
                "key": api_key,
                "cx": search_engine_id,
                "q": search_query,
                "num": num_results
            }

            logger.info(f"Searching Google for: {search_query}")
            response = requests.get(WebSearchTool.SEARCH_URL, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract search results
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title"),
                    "link": item.get("link"),
                    "snippet": item.get("snippet"),
                    "displayed_link": item.get("displayLink")
                })

            logger.info(f"Found {len(results)} search results")

            return {
                "query": query,
                "num_results": len(results),
                "results": results
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Web search failed: {str(e)}")
            return {"error": f"Web search failed: {str(e)}"}
        except Exception as e:
            logger.error(f"Unexpected error in web search: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}
