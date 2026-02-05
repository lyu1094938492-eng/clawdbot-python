import requests
import json

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer any_key"
}

data = {
    "model": "qwen3-coder-plus",
    "messages": [
        {"role": "user", "content": "帮我查一下旧金山的天气怎么样？"}
    ],
    "stream": False
}

print("正在发送天气查询请求 (预期触发 weather 技能注入)...")
response = requests.post(url, headers=headers, json=data)

if response.status_code == 200:
    print("✅ 请求成功!")
    result = response.json()
    reply = result['choices'][0]['message']['content']
    print("\nAI 回复内容:")
    print("-" * 40)
    print(reply)
    print("-" * 40)
else:
    print(f"❌ 错误: {response.status_code}")
    print(response.text)
