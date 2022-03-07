from typing import Optional, List, Dict, Any, Union
import discord
from personate.utils.logger import logger
import random

class UpdateableMessageWrapper:
    '''This contains a discord.WebhookMessage or a discord.Message object, and has a method for updating its content, by passing down the kwargs from the call.'''
    def __init__(self, message: discord.Message):
        self.message = message
    async def update(self, **kwargs):
        return await self.message.edit(**kwargs)

class Face:
    """
    This is maybe one of the simplest classes in the library. It manages webhooks and posts as the webhook with a specific appearance (avatar_url and username).
    """

    def __init__(
        self,
        bot: discord.Bot,
        avatar_url: str,
        username: str,
        loading_message: Optional[Union[List[str], str]] = None,
    ):
        self.bot = bot
        self.avatar_url = avatar_url
        self.username = username
        self.loading_message = loading_message
        self.webhooks: Dict[int, discord.Webhook] = {}
        logger.debug(
            f"Face created with avatar_url: {avatar_url} and username: {username}"
        )

    async def get_webhook(self, channel_id: int) -> Optional[discord.Webhook]:
        channel = self.bot.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):

            def predicate(webhook: discord.Webhook):
                return webhook.user == self.bot.user

            webhooks: List[discord.Webhook] = await channel.webhooks()
            webhook = discord.utils.find(lambda m: predicate(m), webhooks)
            if not webhook:
                if self.bot.user:
                    try:
                        webhook = await channel.create_webhook(name=self.bot.user.name)
                    except discord.HTTPException:
                        pass
            if webhook:
                return webhook
        logger.debug(
            f"Was unable to find a webhook for channel: {channel_id}. This might be because the bot lacks the relevant permissions (Manage Webhooks), or for some other bizarre reason."
        )
        return None

    async def send_custom(
        self,
        channel_id: int,
        content: str,
        avatar_url: str,
        username: str,
        **kwargs,
    ) -> UpdateableMessageWrapper:
        """Flexible method that handles different cases."""
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel) or not channel:
            raise ValueError(
                f"Channel: {channel_id} is not a valid text channel. Please provide a valid text channel id."
            )
        webhook = await self.get_webhook(channel.id)
        logger.debug(f"Sent message to channel: {channel.id} with content: {content}")
        if webhook:
            message = await webhook.send(
                content=content,
                avatar_url=avatar_url,
                username=username,
                wait=True,
                **kwargs,
            )
        else:
            message = await channel.send(content, **kwargs)
        return UpdateableMessageWrapper(message)

    async def send_loading(self, channel_id: int) -> UpdateableMessageWrapper:
        if not self.loading_message:
            self.loading_message = "...thinking..."
        if isinstance(self.loading_message, str):
            loading_message = self.loading_message
        else:
            loading_message = random.choice(self.loading_message)
        logger.debug(
            f"Sent loading message to channel: {int} with content: {loading_message}"
        )
        return await self.send_custom(
            channel_id, loading_message, self.avatar_url, self.username
        )

    async def send(self, channel_id: int, content: str, **kwargs) -> UpdateableMessageWrapper:
        logger.debug(f"Sent message to channel: {channel_id} with content: {content}")
        return await self.send_custom(
            channel_id, content, self.avatar_url, self.username, **kwargs
        )