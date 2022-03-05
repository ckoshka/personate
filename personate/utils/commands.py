import discord
from typing import Dict, Callable, Optional

class CommandRegister:
    def __init__(self, bot: discord.Bot, name: str):
        self.bot = bot
        self.prefix = f"{name}!"
        self.owner_id = bot.owner_id
        self.functions: Dict[str, Callable] = dict()
        self.conditions: Dict[str, Callable] = dict()
        self.bot.add_listener(func=self.process_arguments, name="on_message")
    def register(self, owner: bool = True, condition: Optional[Callable] = None) -> Callable:
        if not condition:
            condition = lambda msg: True
        def register_outer(self, func: Callable) -> Callable:
            nonlocal condition
            funcname = func.__name__
            self.functions[self.prefix + funcname] = func
            if owner:
                def new_condition(m: discord.Message) -> bool:
                    return condition(m) and m.author.id == self.owner_id
                condition = new_condition
            self.conditions[func.__name__] = condition
            return func
        return register_outer
    async def process_arguments(self, msg: discord.Message):
        content = msg.content
        if not content.startswith(self.prefix):
            return
        command = content.split(" ")[0].lower()
        if not self.conditions[command](msg):
            return
        try:
            func = self.functions[command]
        except KeyError:
            return
        content = content.replace(command, "").strip()
        await func(msg, content)