import asyncio
import httpx
import json
import sys
import time
from websockets.client import connect

BASE_URL = "http://127.0.0.1:8080"
WS_URL = "ws://127.0.0.1:8000/ws"

PUBLIC_PATHS = ["/", "/health", "/health/live", "/health/ready", "/metrics", "/docs"]

async def test_api():
    print("开始 Public API 接口可用性测试...")
    async with httpx.AsyncClient() as client:
        for path in PUBLIC_PATHS:
            try:
                r = await client.get(f"{BASE_URL}{path}")
                status = "OK" if r.status_code < 400 else "FAIL"
                print(f"[{status}] 接口 {path}: {r.status_code}")
            except Exception as e:
                print(f"[ERR] 接口 {path} 访问失败: {e}")

        # 尝试访问公开的模型列表 (可能会 401/403，仅以此测试流程)
        try:
            r = await client.get(f"{BASE_URL}/v1/models")
            print(f"[INFO] OpenAI 模型列表: {r.status_code} (预期 200 或 401)")
        except Exception as e:
            print(f"[ERR] OpenAI 模型列表访问失败: {e}")

WS_URL = "ws://127.0.0.1:18789"

async def test_websocket():
    print(f"开始 Gateway WebSocket 测试 ({WS_URL})...")
    try:
        async with connect(WS_URL) as websocket:
            # 发送 Gateway 协议格式的健康检查请求
            request = {
                "type": "req",
                "id": "verify-health",
                "method": "health",
                "params": {}
            }
            await websocket.send(json.dumps(request))
            response = await websocket.recv()
            data = json.loads(response)
            if data.get("ok") is True:
                print(f"[OK] Gateway WebSocket 响应正常: {data.get('payload')}")
            else:
                print(f"[WARN] Gateway 响应非预期: {data}")
    except Exception as e:
        print(f"[ERR] Gateway WebSocket 测试失败: {e}")

async def test_chat_completion(message: str):
    print(f"\n测试 [非流式] 对话接口: '{message}'")
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": "openai-compatible/qwen-plus",
            "messages": [{"role": "user", "content": message}],
            "stream": False
        }
        try:
            r = await client.post(f"{BASE_URL}/v1/chat/completions", json=payload)
            if r.status_code == 200:
                resp_json = r.json()
                content = resp_json["choices"][0]["message"]["content"]
                print(f"[OK] 收到回复: {content}")
            else:
                print(f"[FAIL] 对话接口失败: {r.status_code} - {r.text}")
        except Exception as e:
            print(f"[ERR] 对话接口访问出错: {e}")
            if 'r' in locals():
                print(f"DEBUG: {r.text}")

async def test_chat_completion_stream(message: str):
    print(f"\n测试 [流式] 对话接口: '{message}'")
    async with httpx.AsyncClient(timeout=30.0) as client:
        payload = {
            "model": "openai-compatible/qwen-plus",
            "messages": [{"role": "user", "content": message}],
            "stream": True
        }
        try:
            async with client.stream("POST", f"{BASE_URL}/v1/chat/completions", json=payload) as response:
                if response.status_code != 200:
                    print(f"[FAIL] 流式接口失败: {response.status_code}")
                    return
                print("[OK] 开始接收流式响应: ", end="", flush=True)
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            data = json.loads(data_str)
                            delta = data["choices"][0]["delta"].get("content")
                            if delta:
                                print(delta, end="", flush=True)
                        except:
                            pass
                print("\n[OK] 流式传输完成")
        except Exception as e:
            print(f"\n[ERR] 流式接口访问出错: {e}")

async def main():
    # 稍微等待服务启动
    print("等待服务就绪 (5s)...")
    await asyncio.sleep(5)
    await test_api()
    await test_websocket()
    
    msg = "我的桌面上有哪些文件？"
    await test_chat_completion(msg)
    await test_chat_completion_stream(msg)

if __name__ == "__main__":
    asyncio.run(main())
