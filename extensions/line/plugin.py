"""line channel plugin"""

from clawdbot.channels.line import LINEChannel
from clawdbot.channels.registry import get_channel_registry


def register(api):
    """Register line channel"""
    channel = LINEChannel()
    registry = get_channel_registry()
    registry.register(channel)
