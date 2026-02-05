"""
Tool to read skill documentation
"""

import logging
from typing import Any
from .base import AgentTool, ToolResult
from .skill_loader import get_skill_provider

logger = logging.getLogger(__name__)

class ReadSkillTool(AgentTool):
    """Tool to read the full documentation and instructions for a specialized skill"""

    def __init__(self):
        super().__init__()
        self.name = "read_skill"
        self.description = "Read full usage instructions and examples for a specific skill"
        self.skill_provider = get_skill_provider()

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "The name of the skill to read (e.g., 'weather', 'obsidian', 'github')",
                }
            },
            "required": ["skill_name"],
        }

    async def execute(self, params: dict[str, Any]) -> ToolResult:
        skill_name = params.get("skill_name")
        if not skill_name:
            return ToolResult(success=False, content="", error="skill_name is required")

        skill = self.skill_provider.skills.get(skill_name)
        if not skill:
            available = ", ".join(self.skill_provider.skills.keys())
            return ToolResult(
                success=False, 
                content="", 
                error=f"Skill '{skill_name}' not found. Available skills: {available}"
            )

        content = f"# Skill: {skill['name']}\n\n"
        content += f"Description: {skill['description']}\n"
        content += f"Instructions:\n{skill['instructions']}\n"
        
        return ToolResult(success=True, content=content)
