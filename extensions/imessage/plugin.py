"""imessage channel plugin"""

from clawdbot.channels.imessage import iMessageChannel
from clawdbot.channels.registry import get_channel_registry


def register(api):
    """Register imessage channel"""
    channel = iMessageChannel()
    registry = get_channel_registry()
    registry.register(channel)
