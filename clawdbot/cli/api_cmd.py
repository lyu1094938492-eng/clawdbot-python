"""API server management commands"""

import asyncio
import typer
from rich.console import Console

from ..agents.runtime import AgentRuntime
from ..agents.session import SessionManager
from ..channels.registry import ChannelRegistry
from ..config import get_settings
from ..monitoring import setup_logging
from ..api import run_api_server

console = Console()
api_app = typer.Typer(help="API server management")

@api_app.command("start")
def api_start(
    host: str | None = typer.Option(None, help="Host to bind to"),
    port: int | None = typer.Option(None, help="Port to bind to"),
):
    """Start API server"""

    async def run():
        settings = get_settings()

        # Setup logging
        setup_logging(
            level=settings.monitoring.log_level, format_type=settings.monitoring.log_format
        )

        # Create components
        runtime = AgentRuntime(
            model=settings.agent.model,
            api_key=settings.agent.api_key,
            base_url=settings.agent.base_url,
            enable_context_management=settings.agent.enable_context_management,
        )
        session_manager = SessionManager(settings.workspace_dir)
        channel_registry = ChannelRegistry()

        # Run server
        actual_host = host or settings.api.host
        actual_port = port or settings.api.port

        console.print(f"\n🚀 Starting API server on {actual_host}:{actual_port}")
        console.print(f"📚 Docs: http://{actual_host}:{actual_port}/docs\n")

        await run_api_server(
            host=actual_host,
            port=actual_port,
            runtime=runtime,
            session_manager=session_manager,
            channel_registry=channel_registry,
        )

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console.print("\n✅ Server stopped")
