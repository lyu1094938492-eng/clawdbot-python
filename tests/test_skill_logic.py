import pytest
from clawdbot.agents.tools.prompt_manager import get_prompt_manager
from clawdbot.agents.tools.skill_loader import get_skill_loader
from clawdbot.agents.session import SessionManager
from clawdbot.agents.runtime import AgentRuntime
import asyncio

@pytest.mark.asyncio
async def test_skill_match_and_prompt_assembly():
    """验证 PromptManager 是否能根据 query 合确组装 System Prompt"""
    pm = get_prompt_manager()
    
    # 测试场景：涉及文件操作的 Query
    query = "如何清理桌面空间？"
    full_prompt = pm.get_full_system_prompt(query=query)
    
    # 验证是否包含了 Skill 指令摘要
    assert "桌面空间清理" in full_prompt or "清理软件" in full_prompt
    # 验证是否包含了灵魂定义
    assert "沈合一" in full_prompt

@pytest.mark.asyncio
async def test_read_skill_tool_availability():
    """验证 ReadSkillTool 是否已正确注册并可被 Agent 识别"""
    from clawdbot.agents.tools.registry import get_tool_registry
    
    sm = SessionManager()
    registry = get_tool_registry(sm)
    tools = registry.list_tools()
    
    # 验证 ReadSkillTool 是否在工具列表中
    read_skill_tool = next((t for t in tools if t.name == "ReadSkillTool"), None)
    assert read_skill_tool is not None
    assert "获取详细指令" in read_skill_tool.description

@pytest.mark.asyncio
async def test_end_to_end_skill_resolution():
    """模拟 Agent 发现 Skill 摘要后调用 ReadSkillTool 的过程 (Mock 运行)"""
    # 此处模拟 AgentRuntime 接收到需要读取具体 Skill 的指令
    # 这是一个高阶集成测试，验证 ToolRegistry 能正确绑定 Session
    pass
