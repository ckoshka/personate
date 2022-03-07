import discord
from typing import Any, Dict, Callable, Optional, Union
from personate.utils.logger import logger

class CommandRegister:
    def __init__(self, bot: discord.Bot, name: str):
        self.bot = bot
        self.prefix = f"{name}!"
        self.functions: Dict[str, Callable] = dict()
        self.conditions: Dict[str, Callable] = dict()
        self.bot.add_listener(func=self.process_arguments, name="on_message")
        self.tied_to: Optional[Any] = None
    def register(self, owner: bool = True, condition: Callable = lambda m: True) -> Callable:
        def register_outer(func: Callable) -> Callable:
            funcname = func.__name__
            self.functions[self.prefix + funcname] = func
            if owner:
                async def new_condition(m: discord.Message) -> bool:
                    return condition(m) and isinstance(m.author, discord.User) and await self.bot.is_owner(m.author)
            else:
                async def new_condition(m: discord.Message) -> bool:
                    return condition(m)
            self.conditions[self.prefix + func.__name__] = new_condition
            return func
        return register_outer
    async def process_arguments(self, msg: discord.Message):
        content = msg.content
        if not content.startswith(self.prefix):
            return
        command = content.split(" ")[0]
        if not await self.conditions[command](msg):
            await msg.channel.send("You do not have permission to use this command.")
            return
        try:
            func = self.functions[command]
        except KeyError:
            await msg.channel.send("Command not found.")
            return
        content = content.replace(command, "").strip()
        await func(self.tied_to, msg, content)