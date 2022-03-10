from typing import Optional, List, Dict, Any, Union
import discord
from personate.swarm.internal_message import InternalMessage
from personate.utils.logger import logger
import random


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
        channel: discord.TextChannel,
        content: str,
        avatar_url: str,
        username: str,
        **kwargs,
    ):
        """Flexible method that handles different cases."""
        webhook = await self.get_webhook(channel.id)
        logger.debug(f"Sent message to channel: {channel.id} with content: {content}")
        if webhook:
            return await webhook.send(
                content=content,
                avatar_url=avatar_url,
                username=username,
                wait=True,
                **kwargs,
            )
        else:
            return await channel.send(content, **kwargs)

    async def send_loading(self, channel: discord.TextChannel):
        if not self.loading_message:
            self.loading_message = "...thinking..."
        if isinstance(self.loading_message, str):
            loading_message = self.loading_message
        else:
            loading_message = random.choice(self.loading_message)
        logger.debug(
            f"Sent loading message to channel: {channel.id} with content: {loading_message}"
        )
        return await self.send_custom(
            channel, loading_message, self.avatar_url, self.username
        )

    async def send(self, channel: discord.TextChannel, content: str, **kwargs):
        logger.debug(f"Sent message to channel: {channel.id} with content: {content}")
        return await self.send_custom(
            channel, content, self.avatar_url, self.username, **kwargs
        )

    async def update(
        self,
        agent_message: InternalMessage,
        original_loading_message: discord.WebhookMessage,
    ):
        files: list[discord.File] = []
        if isinstance(agent_message.files, list):
            for f in agent_message.files:
                if isinstance(f, discord.File):
                    files.append(f)

        if agent_message.external_content and isinstance(
            agent_message.embeds[0], discord.Embed
        ):
            await original_loading_message.edit(
                content=agent_message.external_content,
                embeds=agent_message.embeds,
                files=files,
            )
    #await self.parent.face.reply_and_delete(internal_message_agent, external_message_agent, external_message_user)

    async def reply_and_delete(
        self,
        internal_message_agent: InternalMessage,
        external_message_agent: discord.WebhookMessage,
        external_message_user: discord.Message,
    ):
        await external_message_agent.delete()
        await external_message_user.reply(
            content=internal_message_agent.external_content,
            embed=internal_message_agent.embeds[0],
        )