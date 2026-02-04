"""mattermost channel plugin"""

from clawdbot.channels.mattermost import MattermostChannel
from clawdbot.channels.registry import get_channel_registry


def register(api):
    """Register mattermost channel"""
    channel = MattermostChannel()
    registry = get_channel_registry()
    registry.register(channel)
