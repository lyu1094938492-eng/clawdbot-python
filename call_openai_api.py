"""
调用 ClawdBot 的 OpenAI 兼容接口
使用 /v1/chat/completions 端点
"""

import requests
import json

# API 配置
API_BASE_URL = "http://localhost:8000"
ENDPOINT = "/v1/chat/completions"

# 构造请求
url = f"{API_BASE_URL}{ENDPOINT}"

# 请求体 - 使用 OpenAI 格式
payload = {
    "model": "qwen3-coder-plus",  # 使用你配置的模型
    "messages": [
        {
            "role": "user",
            "content": "我的桌面上哪个文件夹的最占用空间"
        }
    ],
    "stream": False,  # 非流式响应
    "max_tokens": 4096
}

# 请求头
headers = {
    "Content-Type": "application/json"
}

print("=" * 60)
print("调用 OpenAI 兼容接口: /v1/chat/completions")
print("=" * 60)
print(f"\n请求 URL: {url}")
print(f"\n请求体:\n{json.dumps(payload, ensure_ascii=False, indent=2)}")
print("\n" + "=" * 60)

try:
    # 发送 POST 请求
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    
    # 检查响应状态
    print(f"\n响应状态码: {response.status_code}")
    
    if response.status_code == 200:
        # 解析响应
        result = response.json()
        print(f"\n完整响应:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 提取 AI 回复内容
        if "choices" in result and len(result["choices"]) > 0:
            assistant_message = result["choices"][0]["message"]["content"]
            print("\n" + "=" * 60)
            print("AI 回复:")
            print("=" * 60)
            print(assistant_message)
            print("=" * 60)
            
            # 显示 token 使用情况
            if "usage" in result:
                usage = result["usage"]
                print(f"\nToken 使用情况:")
                print(f"  - 提示 tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"  - 完成 tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"  - 总计 tokens: {usage.get('total_tokens', 'N/A')}")
    else:
        print(f"\n请求失败!")
        print(f"响应内容:\n{response.text}")
        
except requests.exceptions.ConnectionError:
    print("\n❌ 连接失败! 请确保后端服务正在运行 (http://localhost:8000)")
except requests.exceptions.Timeout:
    print("\n❌ 请求超时! AI 可能正在处理复杂任务...")
except Exception as e:
    print(f"\n❌ 发生错误: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
