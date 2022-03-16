import discord
from typing import Any, Dict, Callable, Optional, Union
from personate.utils.logger import logger
import ast
import inspect


class CommandRegister:
    def __init__(self, bot: discord.Bot, name: str):
        self.bot = bot
        self.prefix = f"{name}!"
        self.functions: Dict[str, Callable] = dict()
        self.wrapped_functions: Dict[str, Callable] = dict()
        self.conditions: Dict[str, Callable] = dict()
        self.bot.add_listener(func=self.process_arguments, name="on_message")
        self.tied_to: Optional[Any] = None

    def register(
        self, owner: bool = True, condition: Callable = lambda m: True
    ) -> Callable:
        def register_outer(func: Callable) -> Callable:
            funcname = func.__name__
            self.functions[self.prefix + funcname] = func
            if owner:

                async def new_condition(m: discord.Message) -> bool:
                    return condition(m) and await self.bot.is_owner(m.author)  # type: ignore

            else:

                async def new_condition(m: discord.Message) -> bool:
                    return condition(m)

            self.conditions[self.prefix + func.__name__] = new_condition

            async def inner(*args, **kwargs):
                ctx = kwargs.pop("ctx")
                logger.debug(f"Arguments: {args}")
                logger.debug(f"Keyword arguments: {kwargs}")
                result = await func(*args, **kwargs)
                if result:
                    await ctx.channel.send("```" + result + "```")

            async def async_generator_inner(*args, **kwargs):
                ctx = kwargs.pop("ctx")
                async for result in func(*args, **kwargs):
                    if result:
                        await ctx.channel.send(result)

            if inspect.isasyncgenfunction(func):
                self.wrapped_functions[self.prefix + funcname] = async_generator_inner
                return async_generator_inner
            else:
                self.wrapped_functions[self.prefix + funcname] = inner
                return inner

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
        number_of_args = func.__code__.co_argcount - 1
        number_of_quotes = content.count('"')

        func = self.wrapped_functions[command]

        logger.debug(f"Number of args: {number_of_args}")
        logger.debug(f"Number of quotes: {number_of_quotes}")
        if number_of_quotes % 2 != 0:
            await msg.channel.send("Unbalanced quotes.")
            return
        # if number_of_quotes / 2 != number_of_args and not number_of_quotes == 0:
        # await msg.channel.send("Incorrect number of arguments.")
        # return
        # Check if there is a positional arg called "ctx"
        if "ctx" in func.__code__.co_varnames:
            if not number_of_quotes == 0:
                args: list[str] = ast.literal_eval(content)
                logger.debug(f"Args: {args}")
                if self.tied_to:
                    await func(self.tied_to, msg, *args, ctx=msg)
                else:
                    await func(msg, *args, ctx=msg)
            else:
                if self.tied_to:
                    await func(self.tied_to, msg, content, ctx=msg)
                else:
                    await func(msg, content, ctx=msg)
        else:
            if not number_of_quotes == 0:
                args: list[str] = ast.literal_eval(content)
                logger.debug(f"Args: {args}")
                if self.tied_to:
                    await func(self.tied_to, *args, ctx=msg)
                else:
                    await func(*args, ctx=msg)
            else:
                if self.tied_to:
                    await func(self.tied_to, content, ctx=msg)
                else:
                    await func(content, ctx=msg)
        # This sucks and I hate how it looks, feel free to improve it