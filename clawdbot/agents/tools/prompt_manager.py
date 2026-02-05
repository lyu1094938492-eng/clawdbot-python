"""
Prompt manager for ClawdBot
Collates base prompts, soul, and skills into a final system prompt.
"""

import logging
from pathlib import Path
from .skill_loader import get_skill_provider

logger = logging.getLogger(__name__)

class PromptManager:
    """Manages loading and formatting system prompts"""
    
    def __init__(self, prompt_dir: str | Path | None = None):
        if prompt_dir is None:
            # Base directory for prompts
            base_dir = Path(__file__).parent.parent.parent.parent
            self.prompt_dir = base_dir / "clawdbot" / "prompts"
        else:
            self.prompt_dir = Path(prompt_dir)
            
        self.skill_provider = get_skill_provider()

    def get_full_system_prompt(self, query: str | None = None) -> str:
        """Get the full assembled system prompt, optionally specialized for a query"""
        base_prompt = self._load_file("base.md")
        soul_prompt = self._load_file("soul.md")
        
        # Determine which skills to inject based on query
        matched_skills = None
        if query:
            matched_skills = self.skill_provider.find_skills(query)
            
        skills_segment = self.skill_provider.get_system_prompt_segment(matched_skills)
        
        # Replace placeholders in base prompt
        full_prompt = base_prompt.replace("{{SKILLS_SUMMARY}}", skills_segment)
        
        # Append soul
        if soul_prompt:
            full_prompt += f"\n<personality>\n{soul_prompt}\n</personality>"
            
        logger.info(f"Assembled system prompt. Length: {len(full_prompt)} chars (Matched skills: {len(matched_skills) if matched_skills else 0})")
        return full_prompt

    def _load_file(self, filename: str) -> str:
        """Load a prompt file from the prompts directory"""
        file_path = self.prompt_dir / filename
        if not file_path.exists():
            logger.warning(f"Prompt file not found: {file_path}")
            return ""
        return file_path.read_text(encoding="utf-8")

_global_manager = None

def get_prompt_manager(prompt_dir: str | None = None) -> PromptManager:
    """Get or create global PromptManager"""
    global _global_manager
    if _global_manager is None:
        _global_manager = PromptManager(prompt_dir)
    return _global_manager
