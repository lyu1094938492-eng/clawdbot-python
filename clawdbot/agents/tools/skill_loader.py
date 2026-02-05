"""
Skill loader for ClawdBot
Loads skill descriptions from the skills/ directory.
"""

import os
import yaml
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SkillProvider:
    """Provides skill information loaded from markdown files"""
    
    def __init__(self, skills_dir: str | Path):
        self.skills_dir = Path(skills_dir)
        self.skills = {}
        self.load_skills()

    def load_skills(self):
        """Scan skills directory and load SKILL.md files"""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return

        for skill_path in self.skills_dir.iterdir():
            if skill_path.is_dir():
                skill_file = skill_path / "SKILL.md"
                if skill_file.exists():
                    try:
                        skill_info = self._parse_skill_file(skill_file)
                        if skill_info:
                            self.skills[skill_info["name"]] = skill_info
                    except Exception as e:
                        logger.error(f"Failed to load skill from {skill_file}: {e}")

    def _parse_skill_file(self, file_path: Path) -> dict | None:
        """Parse SKILL.md with YAML frontmatter"""
        content = file_path.read_text(encoding="utf-8")
        
        # Split frontmatter
        if not content.startswith("---"):
            return None
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
            
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2].strip()
        
        return {
            "name": frontmatter.get("name"),
            "description": frontmatter.get("description"),
            "instructions": body,
            "tags": frontmatter.get("tags", []),
            "version": frontmatter.get("version", "1.0.0")
        }

    def find_skills(self, query: str) -> list[dict]:
        """Find relevant skills based on query keywords and tags"""
        query_lower = query.lower()
        matched = []
        for skill in self.skills.values():
            # Check name, description, and tags
            items_to_check = [skill["name"].lower(), skill["description"].lower()]
            items_to_check.extend([tag.lower() for tag in skill.get("tags", [])])
            
            if any(item in query_lower for item in items_to_check):
                matched.append(skill)
        return matched

    def get_system_prompt_segment(self, matched_skills: list[dict] | None = None) -> str:
        """Generate a summarized system prompt segment. 
        If matched_skills is provided, include their full instructions.
        Otherwise, only show a list of names.
        """
        if not self.skills:
            return "No specialized skills loaded."
            
        segment = "\n### SPECIALIZED SKILLS\n"
        
        if matched_skills:
            segment += "The following relevant skills have been dynamically loaded based on your request:\n\n"
            for skill in matched_skills:
                segment += f"#### Skill: {skill['name']}\n"
                segment += f"Description: {skill['description']}\n"
                segment += f"Instructions:\n{skill['instructions']}\n\n"
            
            # Also list others as one-liners
            other_names = [s["name"] for s in self.skills.values() if s["name"] not in [m["name"] for m in matched_skills]]
            if other_names:
                segment += f"Other available skills: {', '.join(other_names)}. (Use 'read_skill' to see details if needed)\n"
        else:
            segment += "Use 'read_skill' to see details for any of the following available skills:\n"
            segment += f"Available: {', '.join(self.skills.keys())}\n"
        
        return segment

_global_provider = None

def get_skill_provider(skills_dir: str | None = None) -> SkillProvider:
    """Get or create global SkillProvider"""
    global _global_provider
    if _global_provider is None:
        if skills_dir is None:
            # Detect skills directory relative to this file
            base_dir = Path(__file__).parent.parent.parent.parent
            skills_dir = base_dir / "skills"
            
        _global_provider = SkillProvider(skills_dir)
    return _global_provider
