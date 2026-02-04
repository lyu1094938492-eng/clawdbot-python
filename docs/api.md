# ClawdBot API Documentation

Welcome to the ClawdBot API documentation. This document provides a comprehensive overview of the available interfaces for interacting with the ClawdBot agent platform.

## 1. Base URL
- **REST API**: `http://<host>:<port>` (Default port: `8000`)
- **OpenAI Compatible**: `http://<host>:<port>/v1`
- **Gateway WebSocket**: `ws://<host>:<port>` (Default port: `8001`)

---

## 2. Authentication
Most endpoints require an API key passed in the `X-API-Key` or `Authorization` header.
```bash
Authorization: Bearer <your_api_key>
# OR
X-API-Key: <your_api_key>
```

---

## 3. REST API Endpoints

### 3.1 Agent Interactions
- **`POST /agent/chat`**: Execute a synchronous agent turn.
  - **Payload**:
    ```json
    {
      "session_id": "string",
      "message": "string",
      "model": "string (optional)",
      "max_tokens": 4096
    }
    ```
  - **Response**: `AgentResponse` containing the text result.

- **`GET /agent/sessions`**: List all active session IDs.
- **`GET /agent/sessions/{session_id}`**: Retrieve message history and metadata for a session.
- **`DELETE /agent/sessions/{session_id}`**: Delete a session and its history.

### 3.2 Channel Management
- **`GET /channels`**: List all registered channels (Slack, Telegram, etc.).
- **`POST /channels/send`**: Send a message through a specific channel.
  - **Payload**:
    ```json
    {
      "channel_id": "string",
      "target": "string",
      "text": "string"
    }
    ```

### 3.3 System Health & Monitoring
- **`GET /health`**: Comprehensive health check.
- **`GET /metrics`**: Service metrics in JSON format.
- **`GET /metrics/prometheus`**: Metrics in Prometheus format.

---

## 4. OpenAI Compatible API
ClawdBot supports a subset of the OpenAI API, making it a drop-in replacement for many tools.

- **`GET /v1/models`**: List available models.
- **`POST /v1/chat/completions`**: Create a chat completion (supports streaming).
  - Matches the standard OpenAI schema.
  - Supports `stream: true`.

---

## 5. Gateway WebSocket API (Real-time)
For low-latency, real-time streaming and event-driven interactions.

### 5.1 Communication Protocol
Messages use a framed JSON format:
```json
{
  "id": "unique_request_id",
  "type": "req",
  "method": "method_name",
  "params": {}
}
```

### 5.2 Available Methods
| Method | Description | Params |
| :--- | :--- | :--- |
| `connect` | Handshake & authentication | `{ "client": { "name": "..." }, "maxProtocol": 1 }` |
| `health` | Connectivity check | N/A |
| `status` | Server & agent status | N/A |
| `sessions.list` | List active sessions | N/A |
| `chat.history` | Get session history | `{ "sessionKey": "..." }` |
| `agent` | **Run Agent (Async)** | `{ "message": "...", "sessionId": "..." }` |

### 5.3 Streaming Events (Server -> Client)
When using the `agent` method, the server streams the following events:
```json
{
  "event": "agent",
  "payload": {
    "runId": "...",
    "type": "text_delta | tool_use | tool_result | done",
    "data": { ... }
  }
}
```

---

## 6. Error Handling
All APIs use standard HTTP status codes or Gateway error frames.
- `401 / AUTH_REQUIRED`: Missing/invalid API key.
- `404 / METHOD_NOT_FOUND`: Resource or method does not exist.
- `503`: Service or component not initialized.
