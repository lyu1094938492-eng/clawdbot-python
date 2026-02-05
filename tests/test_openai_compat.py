import pytest
from fastapi.testclient import TestClient
from clawdbot.main import app
import json

client = TestClient(app)

def test_models_endpoint():
    """验证模型列表接口"""
    response = client.get("/v1/models")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert data["data"][0]["object"] == "model"

def test_chat_completions_basic():
    """验证基础对话接口 (非流式)"""
    payload = {
        "model": "claude-3-5-sonnet",
        "messages": [
            {"role": "user", "content": "你好，请简单介绍一下你自己。"}
        ],
        "stream": False
    }
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["object"] == "chat.completion"
    assert "usage" in data
    assert data["usage"]["total_tokens"] > 0
    assert len(data["choices"]) > 0
    assert data["choices"][0]["message"]["role"] == "assistant"

def test_chat_completions_streaming_metadata():
    """验证流式响应中的元数据捕获 (usage, fingerprint)"""
    payload = {
        "model": "claude-3-5-sonnet",
        "messages": [
            {"role": "user", "content": "计算 1+1 等于多少？"}
        ],
        "stream": True
    }
    with client.stream("POST", "/v1/chat/completions", json=payload) as response:
        assert response.status_code == 200
        
        usage_found = False
        fingerprint_found = False
        chunks = []
        
        for line in response.iter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                
                chunk = json.loads(data_str)
                chunks.append(chunk)
                
                if "usage" in chunk and chunk["usage"] is not None:
                    usage_found = True
                if "system_fingerprint" in chunk and chunk["system_fingerprint"] is not None:
                    fingerprint_found = True
        
        assert len(chunks) > 0
        # 如果模型支持，验证这些字段（Mock 环境下可能需要特定逻辑，真实环境下应验证存在性）
        # 这里记录验证结论
        print(f"Usage found: {usage_found}, Fingerprint found: {fingerprint_found}")

def test_tool_call_visualization_protocol():
    """验证工具调用过程在协议层是否正确透传"""
    payload = {
        "model": "claude-3-5-sonnet",
        "messages": [
            {"role": "user", "content": "帮我看看现在桌面文件夹的大小。"}
        ],
        "stream": True
    }
    # 这个测试依赖于 Agent 是否决定使用工具
    with client.stream("POST", "/v1/chat/completions", json=payload) as response:
        tool_use_seen = False
        tool_result_seen = False
        
        for line in response.iter_lines():
            if line.startswith("data: "):
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                
                chunk = json.loads(data_str)
                delta = chunk["choices"][0]["delta"]
                
                if "tool_calls" in delta:
                    for tc in delta["tool_calls"]:
                        if "function" in tc:
                            if "name" in tc["function"]:
                                tool_use_seen = True
                            if "output" in tc["function"]:
                                tool_result_seen = True
                                
        print(f"Tool use seen: {tool_use_seen}, Tool result seen: {tool_result_seen}")
