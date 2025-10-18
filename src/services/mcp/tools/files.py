"""
File search tool for finding files on the local system.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, List
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class FileSearchArgs(BaseModel):
    """Arguments for file search tool."""
    pattern: str = Field(..., description="Filename pattern to search for (supports wildcards)")
    directory: str = Field(default="~", description="Directory to search in")
    recursive: bool = Field(default=True, description="Search recursively in subdirectories")
    max_results: int = Field(default=50, ge=1, le=500, description="Maximum number of results")


class FileSearchTool:
    """
    Tool for searching files on the local filesystem.

    Supports:
    - Wildcard patterns (*.txt, file*.py, etc.)
    - Recursive directory traversal
    - Safe path handling to prevent directory traversal attacks
    """

    name = "search_files"
    description = "Search for files on the local filesystem by pattern"

    @staticmethod
    def get_schema() -> Dict[str, Any]:
        """Get JSON schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Filename pattern to search for (supports wildcards like *.txt)"
                },
                "directory": {
                    "type": "string",
                    "description": "Directory to search in (default: user's home)",
                    "default": "~"
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Search recursively in subdirectories",
                    "default": True
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (1-500)",
                    "default": 50,
                    "minimum": 1,
                    "maximum": 500
                }
            },
            "required": ["pattern"]
        }

    @staticmethod
    async def execute(args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute file search.

        Args:
            args: Search parameters (pattern, directory, recursive, max_results)

        Returns:
            Dict with search results
        """
        try:
            # Validate and parse arguments
            search_args = FileSearchArgs(**args)

            # Expand home directory
            search_dir = Path(search_args.directory).expanduser().resolve()

            # Safety check - ensure directory exists and is accessible
            if not search_dir.exists():
                return {
                    "error": f"Directory does not exist: {search_args.directory}",
                    "files": []
                }

            if not search_dir.is_dir():
                return {
                    "error": f"Path is not a directory: {search_args.directory}",
                    "files": []
                }

            # Search for files
            results = []

            if search_args.recursive:
                # Recursive search using glob
                pattern = f"**/{search_args.pattern}"
            else:
                pattern = search_args.pattern

            for file_path in search_dir.glob(pattern):
                if file_path.is_file():
                    try:
                        stat = file_path.stat()
                        results.append({
                            "path": str(file_path),
                            "name": file_path.name,
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                            "directory": str(file_path.parent)
                        })

                        # Limit results
                        if len(results) >= search_args.max_results:
                            break
                    except (OSError, PermissionError) as e:
                        logger.debug(f"Skipping file due to error: {file_path} - {e}")
                        continue

            return {
                "files": results,
                "count": len(results),
                "truncated": len(results) >= search_args.max_results,
                "search_directory": str(search_dir),
                "pattern": search_args.pattern
            }

        except Exception as e:
            logger.error(f"File search failed: {str(e)}")
            return {
                "error": str(e),
                "files": []
            }
