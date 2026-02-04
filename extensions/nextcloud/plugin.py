"""nextcloud channel plugin"""

from clawdbot.channels.nextcloud import NextcloudChannel
from clawdbot.channels.registry import get_channel_registry


def register(api):
    """Register nextcloud channel"""
    channel = NextcloudChannel()
    registry = get_channel_registry()
    registry.register(channel)
