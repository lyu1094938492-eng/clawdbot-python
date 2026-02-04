"""bluebubbles channel plugin"""

from clawdbot.channels.bluebubbles import BlueBubblesChannel
from clawdbot.channels.registry import get_channel_registry


def register(api):
    """Register bluebubbles channel"""
    channel = BlueBubblesChannel()
    registry = get_channel_registry()
    registry.register(channel)
