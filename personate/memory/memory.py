from typing import List, Union, Optional, Any
import discord
from sqlitedict import SqliteDict
from personate.swarm.internal_message import InternalMessage


class Memory:
    """
    This class manages access to an internal database, and is usually responsible for retrieving conversation history. But you can also use it to store other events that might be relevant to your Agent / Swarm."""

    @classmethod
    def from_db(cls, db_path: str) -> "Memory":
        """
        Initialise a Memory object from an existing database, or create a new one.
        """
        db = SqliteDict(db_path, autocommit=True)
        return cls(db=db)

    def __init__(self, db: Optional[SqliteDict] = None):
        if db is None:
            db = SqliteDict("messages.sqlite", autocommit=True)
        self.db: SqliteDict = db

    def insert_message(self, message_id: int, message: InternalMessage):
        files = message.files
        del message.files
        self.db[message_id] = message
        message.files = files

    async def retrieve_reply_chain(
        self,
        message: Union[discord.Message, InternalMessage],
        window_size: int = 15,
        max_characters: int = 800,
    ) -> List[InternalMessage]:
        past_messages: List[InternalMessage] = []
        if isinstance(message, discord.Message):
            msg = InternalMessage.from_discord_message(message)
        else:
            msg = message
        last_id = msg.id
        for _ in range(window_size):
            past_messages.append(msg)
            # try:
            # if isinstance(msg, discord.Message) and msg.reference and msg.reference.resolved:
            # last_id = msg.reference.resolved.id
            # except AttributeError:
            if hasattr(msg, "reply_to") and isinstance(msg, InternalMessage):
                last_id = msg.reply_to
            else:
                break
            msg = self.db.get(last_id, None)
            if not msg:
                break
            if sum([len(m.internal_content) for m in past_messages]) > max_characters:
                break
        past_messages.reverse()
        return past_messages

    async def retrieve_all_messages(
        self,
        msg: discord.Message,
        window_size: int = 15,
        max_characters: int = 800,
    ) -> List[InternalMessage]:
        """This function uses pycord's api"""
        history = await msg.channel.history().flatten()
        history.reverse()
        past_messages: List[discord.Message] = []
        for message in history[:window_size]:
            past_messages.append(message)
            if sum([len(m.content) for m in past_messages]) > max_characters:
                break
        past_messages.reverse()
        converted_past_messages: List[InternalMessage] = [
            InternalMessage.from_discord_message(m) for m in past_messages
        ]
        return converted_past_messages
