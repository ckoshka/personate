import discord
from typing import Hashable
import typing
import slugify


class InternalMessage:
    """
    This class is used to represent a message in a conversation. Non-nested (i.e floats, ints, and strings) attributes are shallowly copied over from discord.Message objects, or can be constructed ex nihilo. Most importantly, they contain a "reply_to" attribute with the id of the message being replied to, and an internal_content attribute that represents how the message should be displayed to a Swarm/Agent.
    """

    @classmethod
    def from_discord_message(cls, message: discord.Message) -> "InternalMessage":
        new_instance = cls()
        for attr in message.__slots__:
            if hasattr(message, attr):
                value = getattr(message, attr)
                try:
                    hash(value)
                    setattr(new_instance, attr, value)
                except TypeError:
                    pass
                except AttributeError:
                    pass
        if message.reference and message.reference.resolved:
            setattr(new_instance, "reply_to", message.reference.resolved.id)
        else:
            # Set the reply_to id to 0
            setattr(new_instance, "reply_to", 0)
        setattr(new_instance, "internal_content", message.content)
        setattr(new_instance, "external_content", message.content)
        if isinstance(message.author, discord.Member) and message.author.nick:
            setattr(new_instance, "name", message.author.nick)
        else:
            setattr(new_instance, "name", message.author.name)
        try:
            setattr(new_instance, "author_id", message.author.id)
        except AttributeError:
            pass
        setattr(new_instance, "id", message.id)
        setattr(new_instance, "channel_id", message.channel.id)
        setattr(new_instance, "files", [])
        return new_instance

    @classmethod
    def from_kwargs(cls, **kwargs) -> "InternalMessage":
        new_instance = cls()
        setattr(new_instance, "internal_content", kwargs.get("content", ""))
        setattr(new_instance, "external_content", kwargs.get("content", ""))
        setattr(new_instance, "name", kwargs.get("name", ""))
        setattr(new_instance, "id", kwargs.get("id", ""))
        return new_instance

    __slots__ = (
        "id",
        "name",
        "reply_to",
        "internal_content",
        "external_content",
        "channel_id",
        "embeds",
        "files",
        "author_id",
    )

    def __init__(self):
        self.id = 0
        self.name = ""
        self.reply_to = 0
        self.internal_content = ""
        self.external_content = ""
        self.channel_id = 0
        self.embeds = []
        self.files = []

    def display_as_irc(self) -> str:
        """
        Return the message as an IRC-style string.
        """
        if hasattr(self, "name") and hasattr(self, "internal_content"):
            return f"<{slugify.slugify(self.name, separator=' ', lowercase=False)}>: {self.internal_content}"
        else:
            raise AttributeError(
                "InternalMessage does not have a name or internal_content attribute."
            )

    def __str__(self) -> str:
        return self.display_as_irc()
