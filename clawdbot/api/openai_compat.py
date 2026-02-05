"""
OpenAI-compatible API endpoints

This module provides OpenAI-compatible API endpoints for ClawdBot,
allowing it to be used as a drop-in replacement for OpenAI in many applications.
"""

import logging
import os
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..agents.runtime import AgentRuntime
from ..agents.session import SessionManager
from ..agents.tools.prompt_manager import get_prompt_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])


# Request/Response models following OpenAI API format
class ChatMessage(BaseModel):
    """Chat message"""

    role: str
    content: str | None = None
    tool_calls: list[dict] | None = None
    name: str | None = None


class ChatCompletionRequest(BaseModel):
    """Chat completion request"""

    model: str
    messages: list[ChatMessage]
    temperature: float | None = 1.0
    top_p: float | None = 1.0
    n: int | None = 1
    stream: bool | None = False
    max_tokens: int | None = None
    presence_penalty: float | None = 0.0
    frequency_penalty: float | None = 0.0
    user: str | None = None


class ChatCompletionChoice(BaseModel):
    """Chat completion choice"""

    index: int
    message: ChatMessage
    finish_reason: str | None = None
    logprobs: dict | None = None


class ChatCompletionUsage(BaseModel):
    """Token usage"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    """Chat completion response"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage | None = None
    system_fingerprint: str | None = None


class ChatCompletionChunkDelta(BaseModel):
    """Streaming chunk delta"""

    role: str | None = None
    content: str | None = None
    tool_calls: list[dict] | None = None


class ChatCompletionChunkChoice(BaseModel):
    """Streaming chunk choice"""

    index: int
    delta: ChatCompletionChunkDelta
    finish_reason: str | None = None


class ChatCompletionChunk(BaseModel):
    """Streaming chunk"""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: list[ChatCompletionChunkChoice]
    usage: ChatCompletionUsage | None = None
    system_fingerprint: str | None = None


class ModelInfo(BaseModel):
    """Model information"""

    id: str
    object: str = "model"
    created: int
    owned_by: str


class ModelsResponse(BaseModel):
    """Models list response"""

    object: str = "list"
    data: list[ModelInfo]


# Available models
AVAILABLE_MODELS = [
    ModelInfo(id="claude-opus-4", created=int(time.time()), owned_by="anthropic"),
    ModelInfo(id="claude-sonnet-4", created=int(time.time()), owned_by="anthropic"),
    ModelInfo(id="gpt-4o", created=int(time.time()), owned_by="openai"),
    ModelInfo(id="gpt-4-turbo", created=int(time.time()), owned_by="openai"),
]


# Global instances (set by main API server)
_runtime: AgentRuntime | None = None
_session_manager: SessionManager | None = None


def set_runtime(runtime: AgentRuntime) -> None:
    """Set runtime instance"""
    global _runtime
    _runtime = runtime


def set_session_manager(manager: SessionManager) -> None:
    """Set session manager"""
    global _session_manager
    _session_manager = manager


def _map_model_name(model: str) -> str:
    """Map OpenAI model name to internal model name"""
    # If it's a generic "model" or similar, use the configured model from settings
    if model in ("model", "default", "auto"):
        from ..config import get_settings
        return get_settings().agent.model

    if "/" in model:
        return model

    # If it's just a model name, keep it as is or use the provider from settings if available
    return model


@router.get("/models", response_model=ModelsResponse)
async def list_models():
    """
    List available models

    Returns a list of models compatible with this API.
    """
    return ModelsResponse(data=AVAILABLE_MODELS)


@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(model_id: str):
    """
    Get model information

    Returns information about a specific model.
    """
    for model in AVAILABLE_MODELS:
        if model.id == model_id:
            return model

    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


@router.post("/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest, authorization: str | None = Header(None)
):
    """
    Create chat completion

    Creates a completion for the chat messages.
    Compatible with OpenAI's chat completions API.
    """
    if not _runtime or not _session_manager:
        raise HTTPException(status_code=503, detail="Service not initialized")

    # Generate IDs
    completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(time.time())

    # Map model name
    model = _map_model_name(request.model)

    # Create session for this request
    session_id = request.user or f"openai-compat-{uuid.uuid4().hex[:8]}"
    session = _session_manager.get_session(session_id)

    # Clear session for fresh context (OpenAI-style stateless)
    session.clear()

    # Check for system message
    has_system_msg = any(msg.role == "system" for msg in request.messages)
    
    if not has_system_msg:
        # Get the latest user message as a query for skill matching
        user_query = ""
        for msg in reversed(request.messages):
            if msg.role == "user" and msg.content:
                user_query = msg.content
                break
        
        # Load and Inject fully assembled system prompt (dynamically specialized)
        prompt_manager = get_prompt_manager()
        full_system_prompt = prompt_manager.get_full_system_prompt(query=user_query)
        session.add_system_message(full_system_prompt)

    # Add messages to session
    for msg in request.messages:
        if msg.role == "system":
            session.add_system_message(msg.content)
        elif msg.role == "user":
            session.add_user_message(msg.content)
        elif msg.role == "assistant":
            session.add_assistant_message(msg.content)

    # Create runtime with specified model and global settings
    from ..config import get_settings
    settings = get_settings()
    
    runtime = AgentRuntime(
        model=model,
        base_url=settings.agent.base_url,
        api_key=settings.agent.api_key
    )

    # Get tools from registry
    from ..agents.tools.registry import get_tool_registry
    tool_registry = get_tool_registry(_session_manager)
    tools = tool_registry.list_tools()

    if request.stream:
        # Streaming response
        async def stream_response() -> AsyncIterator[str]:
            start_time = time.time()
            ttfc = None
            try:
                # Send initial chunk with role
                initial_chunk = ChatCompletionChunk(
                    id=completion_id,
                    created=created,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0, delta=ChatCompletionChunkDelta(role="assistant")
                        )
                    ],
                )
                yield f"data: {initial_chunk.model_dump_json()}\n\n"

                # Metadata tracking
                total_usage = None
                system_fingerprint = None

                # Stream content
                async for event in runtime.run_turn(
                    session,
                    "",  # Empty message since we already added messages
                    tools=tools,
                    max_tokens=request.max_tokens or 4096,
                ):
                    if event.type == "assistant":
                        delta = event.data.get("delta", {})
                        if "text" in delta:
                            chunk = ChatCompletionChunk(
                                id=completion_id,
                                created=created,
                                model=request.model,
                                choices=[
                                    ChatCompletionChunkChoice(
                                        index=0,
                                        delta=ChatCompletionChunkDelta(content=delta["text"]),
                                    )
                                ],
                                system_fingerprint=system_fingerprint
                            )
                            yield f"data: {chunk.model_dump_json()}\n\n"
                            
                            if ttfc is None:
                                ttfc = (time.time() - start_time) * 1000
                                logger.info(f"TTFC: {ttfc:.2f}ms")
                    
                    elif event.type == "metadata":
                        system_fingerprint = event.data.get("system_fingerprint")
                        logger.info(f"Metadata received: {event.data}")

                    elif event.type == "usage":
                        total_usage = ChatCompletionUsage(**event.data)
                        logger.info(f"Usage received: {event.data}")

                    elif event.type == "tool_use":
                        # Convert Agent tool_use event to OpenAI tool_calls format
                        tool_call = {
                            "id": f"call_{uuid.uuid4().hex[:12]}",
                            "type": "function",
                            "function": {
                                "name": event.data.get("tool"),
                                "arguments": json.dumps(event.data.get("input", {}))
                            }
                        }
                        chunk = ChatCompletionChunk(
                            id=completion_id,
                            created=created,
                            model=request.model,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionChunkDelta(tool_calls=[tool_call]),
                                )
                            ],
                            system_fingerprint=system_fingerprint
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"
                        logger.info(f"Tool use streamed: {event.data.get('tool')}")

                    elif event.type == "tool_result":
                        # Stream the result of the tool execution
                        chunk = ChatCompletionChunk(
                            id=completion_id,
                            created=created,
                            model=request.model,
                            choices=[
                                ChatCompletionChunkChoice(
                                    index=0,
                                    delta=ChatCompletionChunkDelta(
                                        # Use a custom field or specific role to signal result
                                        tool_calls=[{
                                            "index": 0,
                                            "id": event.data.get("id"),
                                            "type": "function",
                                            "function": {
                                                "name": event.data.get("tool"),
                                                "output": event.data.get("result")
                                            }
                                        }]
                                    ),
                                )
                            ],
                            system_fingerprint=system_fingerprint
                        )
                        yield f"data: {chunk.model_dump_json()}\n\n"
                        logger.info(f"Tool result streamed: {event.data.get('tool')}")

                # Send final chunk with usage if available
                duration = (time.time() - start_time) * 1000
                final_chunk = ChatCompletionChunk(
                    id=completion_id,
                    created=created,
                    model=request.model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0, delta=ChatCompletionChunkDelta(), finish_reason="stop"
                        )
                    ],
                    usage=total_usage,
                    system_fingerprint=system_fingerprint
                )
                
                # We can't easily add duration to standard OpenAI Chunk model without breaking Pydantic,
                # so we log it or add to a private metadata field if we extend the model.
                # Let's add it to a 'performance' field in our models if we want to be '全面'.
                logger.info(f"Stream complete | Duration: {duration:.2f}ms | TTFC: {ttfc if ttfc else 'N/A'}")
                
                yield f"data: {final_chunk.model_dump_json()}\n\n"
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {"error": str(e)}
                yield f"data: {error_chunk}\n\n"

        return StreamingResponse(stream_response(), media_type="text/event-stream")

    else:
        # Non-streaming response
            # Metadata tracking
            total_usage = None
            system_fingerprint = None

            async for event in runtime.run_turn(
                session,
                "",  # Empty message since we already added messages
                tools=tools,
                max_tokens=request.max_tokens or 4096,
            ):
                if event.type == "assistant":
                    delta = event.data.get("delta", {})
                    if "text" in delta:
                        response_text += delta["text"]
                
                elif event.type == "usage":
                    total_usage = ChatCompletionUsage(**event.data)
                
                elif event.type == "metadata":
                    system_fingerprint = event.data.get("system_fingerprint")

            # Fallback estimation if no usage reported
            if not total_usage:
                prompt_tokens = sum(len(m.content) // 4 for m in request.messages if m.content)
                completion_tokens = len(response_text) // 4
                total_usage = ChatCompletionUsage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                )

            return ChatCompletionResponse(
                id=completion_id,
                created=created,
                model=request.model,
                choices=[
                    ChatCompletionChoice(
                        index=0,
                        message=ChatMessage(role="assistant", content=response_text),
                        finish_reason="stop",
                    )
                ],
                usage=total_usage,
                system_fingerprint=system_fingerprint
            )

        except Exception as e:
            logger.error(f"Chat completion error: {e}")
            raise HTTPException(status_code=500, detail=str(e))
