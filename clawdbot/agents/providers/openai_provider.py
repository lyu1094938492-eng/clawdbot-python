"""
OpenAI provider implementation
"""

import logging
import os
from collections.abc import AsyncIterator

from openai import AsyncOpenAI

from .base import LLMMessage, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """
    OpenAI provider

    Supports:
    - GPT-4, GPT-4 Turbo
    - GPT-3.5 Turbo
    - o1, o1-mini, o1-preview
    - Any OpenAI-compatible API (via base_url)

    Example:
        # OpenAI
        provider = OpenAIProvider("gpt-4", api_key="...")

        # OpenAI-compatible (e.g., LM Studio, Ollama with OpenAI compat)
        provider = OpenAIProvider(
            "model-name",
            base_url="http://localhost:1234/v1"
        )
    """

    @property
    def provider_name(self) -> str:
        return "openai"

    def get_client(self) -> AsyncOpenAI:
        """Get OpenAI client"""
        if self._client is None:
            api_key = self.api_key or os.getenv("OPENAI_API_KEY", "not-needed")

            # Support custom base URL for OpenAI-compatible APIs
            kwargs = {"api_key": api_key}
            if self.base_url:
                kwargs["base_url"] = self.base_url

            self._client = AsyncOpenAI(**kwargs)

        return self._client

    async def stream(
        self,
        messages: list[LLMMessage],
        tools: list[dict] | None = None,
        max_tokens: int = 4096,
        **kwargs,
    ) -> AsyncIterator[LLMResponse]:
        """Stream responses from OpenAI"""
        client = self.get_client()

        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            m = {"role": msg.role, "content": msg.content}
            if msg.tool_calls:
                m["tool_calls"] = msg.tool_calls
            if msg.tool_call_id:
                m["tool_call_id"] = msg.tool_call_id
            if msg.name:
                m["name"] = msg.name
            openai_messages.append(m)

        logger.debug(f"Sending messages to OpenAI: {openai_messages}")

        try:
            # Build request parameters
            params = {
                "model": self.model,
                "messages": openai_messages,
                "max_tokens": max_tokens,
                "stream": True,
                **kwargs,
            }

            # Add tools if provided
            if tools:
                params["tools"] = tools
            
            # Enable usage tracking in stream
            params["stream_options"] = {"include_usage": True}

            # Start streaming
            import json
            logger.info(f"OpenAI Request | Model: {self.model} | Messages count: {len(openai_messages)}")
            try:
                with open("openai_request_debug.json", "w", encoding="utf-8") as f:
                    json.dump(params, f, ensure_ascii=False, indent=2)
                logger.info("Wrote OpenAI request params to openai_request_debug.json")
            except Exception as e:
                logger.error(f"Failed to write debug JSON: {e}")
            stream = await client.chat.completions.create(**params)

            # Track tool calls
            tool_calls_buffer = {}

            async for chunk in stream:
                if not chunk.choices:
                    continue

                choice = chunk.choices[0]
                delta = choice.delta

                # Text content
                if delta.content is not None:
                    if delta.content:
                        logger.debug(f"OpenAI delta: {delta.content}")
                    yield LLMResponse(type="text_delta", content=delta.content)

                # Tool calls
                if delta.tool_calls:
                    for tool_call in delta.tool_calls:
                        idx = tool_call.index

                        # Initialize buffer for this tool call
                        if idx not in tool_calls_buffer:
                            tool_calls_buffer[idx] = {
                                "id": tool_call.id or f"call_{idx}",
                                "name": "",
                                "arguments": "",
                            }

                        # Accumulate function name
                        if tool_call.function and tool_call.function.name:
                            tool_calls_buffer[idx]["name"] = tool_call.function.name

                        # Accumulate arguments
                        if tool_call.function and tool_call.function.arguments:
                            tool_calls_buffer[idx]["arguments"] += tool_call.function.arguments

                # Check if done
                if choice.finish_reason:
                    # Emit tool calls if any
                    if tool_calls_buffer:
                        import json

                        tool_calls = []
                        for tc in tool_calls_buffer.values():
                            try:
                                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
                            except json.JSONDecodeError:
                                args = {}

                            tool_calls.append(
                                {
                                    "id": tc["id"],
                                    "type": "function",
                                    "function": {
                                        "name": tc["name"],
                                        "arguments": json.dumps(args) if isinstance(args, dict) else args,
                                    },
                                }
                            )

                        logger.info(f"Yielding tool_call: {tool_calls}")
                        yield LLMResponse(type="tool_call", content=None, tool_calls=tool_calls)

                    yield LLMResponse(
                        type="done", 
                        content=None, 
                        finish_reason=choice.finish_reason,
                        usage=getattr(chunk, "usage", None) if hasattr(chunk, "usage") else None
                    )
                
                # Capture system_fingerprint and usage from chunks that might not have choices
                if hasattr(chunk, "system_fingerprint") and chunk.system_fingerprint:
                    yield LLMResponse(type="metadata", content={"system_fingerprint": chunk.system_fingerprint})
                
                if hasattr(chunk, "usage") and chunk.usage:
                    # In some chunks (especially the last one when using stream_options), usage is present
                    usage_dict = {
                        "prompt_tokens": chunk.usage.prompt_tokens,
                        "completion_tokens": chunk.usage.completion_tokens,
                        "total_tokens": chunk.usage.total_tokens
                    }
                    yield LLMResponse(type="usage", content=usage_dict)

        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            yield LLMResponse(type="error", content=str(e))
