# ClawdBot API 接口文档

本文档详细介绍了如何从外部系统调用 ClawdBot 服务。ClawdBot 提供了两套主要的 API 接口：一套是**原生接口 (Native API)**，另一套是**OpenAI 兼容接口 (OpenAI-Compatible API)**。

## 1. 基础信息

- **API 基地址**: `http://<your-server-ip>:8000`
- **默认端口**: `8000` (可在 `.env` 中通过 `CLAWDBOT_API__PORT` 配置)

### 认证方式 (Authentication)

ClawdBot 使用 API Key 进行认证。您可以通过以下两种方式之一提供 API Key：

1. **HTTP Header (X-API-Key)**: `X-API-Key: clb_your_actual_key`
2. **Authorization Header (Bearer)**: `Authorization: Bearer clb_your_actual_key`

> [!IMPORTANT]
> 系统启动时会在控制台输出默认生成的 API Key。例如：`clb_LSiLEASyWkOwFRKUd2bXTkM9CJnBe0NF3rsgSvNf-AY`。

---

## 2. OpenAI 兼容接口 (推荐)

这套接口完全兼容 OpenAI 的规范，适用于现有的许多 LLM 客户端和工具。

### 对话补全 (Chat Completions)
- **路径**: `POST /v1/chat/completions`
- **功能**: 创建对话完成请求，支持流式 (Streaming) 和工具调用 (Tool Use)。

**请求参数 (JSON)**:
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `model` | `string` | 是 | 模型名称。设为 `model` 将会自动使用 `.env` 中配置的默认模型。 |
| `messages` | `array` | 是 | 消息列表，包含 `role` 和 `content`。 |
| `stream` | `boolean` | 否 | 是否启用流式输出，默认为 `false`。 |
| `max_tokens`| `integer` | 否 | 最大生成数量。 |
| `user` | `string` | 否 | 会话标识符，可用作 `session_id` 以保留上下文。 |

**cURL 示例 (非流式)**:
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer clb_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": false
  }'
```

**cURL 示例 (流式)**:
```bash
curl http://localhost:8000/v1/chat/completions -N \
  -H "Authorization: Bearer clb_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "model",
    "messages": [{"role": "user", "content": "列出桌面文件夹"}],
    "stream": true
  }'
```

---

## 3. 原生 Agent 接口

原生接口更简单，适用于直接集成到自定义系统中。

### 发送消息 (Agent Chat)
- **路径**: `POST /agent/chat`
- **功能**: 向 Agent 发送消息并获取响应。

**请求参数 (JSON)**:
| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :--- | :--- |
| `session_id`| `string` | 是 | 会话 ID，用于保留历史记录。 |
| `message` | `string` | 是 | 用户输入的内容。 |
| `model` | `string` | 否 | 指定使用的模型。 |

**响应 (JSON)**:
```json
{
  "session_id": "test-session",
  "response": "你好！我是 ClawdBot。",
  "metadata": {
    "message_count": 2,
    "model": "qwen-plus"
  }
}
```

---

## 4. 会话管理接口 (Session Management)

### 获取所有会话列表
- **路径**: `GET /agent/sessions`
- **响应**: 返回所有活跃的 `session_id` 及其数量。

### 获取特定会话详情
- **路径**: `GET /agent/sessions/{session_id}`
- **功能**: 查看历史消息记录。

### 删除会话
- **路径**: `DELETE /agent/sessions/{session_id}`
- **功能**: 清除特定会iam ID 的历史记录。

---

## 5. 系统监控 (Monitoring)

### 健康检查 (Health Check)
- **路径**: `GET /health`
- **功能**: 返回系统的整体健康状况，包括运行时环境、会话管理器等。

**cURL 示例**:
```bash
curl http://localhost:8000/health
```

---

## 6. Python 调用示例

使用 `requests` 库调用流式接口：

```python
import requests
import json

url = "http://localhost:8000/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "model": "model",
    "messages": [{"role": "user", "content": "帮我写一段代码"}],
    "stream": True
}

response = requests.post(url, headers=headers, json=data, stream=True)

for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        if decoded_line.startswith('data: '):
            content = decoded_line[6:]
            if content == '[DONE]':
                break
            try:
                chunk = json.loads(content)
                delta = chunk["choices"][0].get("delta", {}).get("content", "")
                print(delta, end="", flush=True)
            except:
                pass
```

> [!TIP]
> 推荐在内网场景下使用 **OpenAI 兼容接口**，因为它能无缝集成大多数主流的 AI 交互工具。
