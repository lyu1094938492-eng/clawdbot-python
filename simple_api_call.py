"""
调用 ClawdBot 的 OpenAI 兼容接口 - 简化版
"""

import requests
import json
import sys

# API 配置
url = "http://localhost:8000/v1/chat/completions"

# 请求体
payload = {
    "model": "qwen3-coder-plus",
    "messages": [
        {
            "role": "user",
            "content": "我的桌面上哪个文件夹的最占用空间"
        }
    ],
    "stream": False,
    "max_tokens": 4096
}

print("正在调用 OpenAI 兼容接口...")
print(f"URL: {url}")
print(f"消息: {payload['messages'][0]['content']}\n")

try:
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
    
    print(f"状态码: {response.status_code}\n")
    
    if response.status_code == 200:
        result = response.json()
        
        # 提取 AI 回复
        if "choices" in result and len(result["choices"]) > 0:
            ai_response = result["choices"][0]["message"]["content"]
            print("=" * 60)
            print("AI 回复:")
            print("=" * 60)
            print(ai_response)
            print("=" * 60)
            
            # Token 使用
            if "usage" in result:
                print(f"\nToken 使用: {result['usage']}")
        else:
            print("未找到回复内容")
            print(f"完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print(f"请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
    sys.exit(1)
