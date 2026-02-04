"""Matrix channel plugin"""

from clawdbot.channels.matrix import MatrixChannel
from clawdbot.channels.registry import get_channel_registry


def register(api):
    """Register Matrix channel"""
    channel = MatrixChannel()
    registry = get_channel_registry()
    registry.register(channel)
