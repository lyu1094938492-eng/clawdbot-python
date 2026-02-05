"""
调用 OpenAI 兼容接口并保存响应到文件
"""

import requests
import json

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

try:
    response = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=60)
    
    if response.status_code == 200:
        result = response.json()
        
        # 保存完整响应到文件
        with open("api_response.json", "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print("✅ API 调用成功!")
        print(f"✅ 完整响应已保存到: api_response.json")
        
        # 提取并显示 AI 回复
        if "choices" in result and len(result["choices"]) > 0:
            ai_response = result["choices"][0]["message"]["content"]
            
            # 保存 AI 回复到单独文件
            with open("ai_response.txt", "w", encoding="utf-8") as f:
                f.write(ai_response)
            
            print(f"✅ AI 回复已保存到: ai_response.txt")
            print("\n" + "=" * 60)
            print("AI 回复内容:")
            print("=" * 60)
            print(ai_response)
            print("=" * 60)
            
            # Token 使用
            if "usage" in result:
                usage = result["usage"]
                print(f"\n📊 Token 使用情况:")
                print(f"   - Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
                print(f"   - Completion tokens: {usage.get('completion_tokens', 'N/A')}")
                print(f"   - Total tokens: {usage.get('total_tokens', 'N/A')}")
        
        print("\n✅ 完成!")
    else:
        print(f"❌ 请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")
        
except Exception as e:
    print(f"❌ 错误: {type(e).__name__}: {e}")
