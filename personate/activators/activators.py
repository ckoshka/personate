from ast import FunctionType
from types import AsyncGeneratorType, CoroutineType, GeneratorType
from typing import (
    AsyncGenerator,
    List,
    Dict,
    Callable,
    Coroutine,
    Generator,
    Any,
    Optional,
    Tuple,
)
import discord
from acrossword import Ranker
import random
import asyncio
import copy
from personate.utils.logger import logger
import inspect
from inspect import signature, Parameter
import rapidfuzz

# We'll turn the logging off for this module by default
logger.disable(__name__)


def get_arg_by_name(name: str, args: Tuple[Any], func: Callable) -> Optional[Any]:
    """Get the index of the argument in the function signature that matches the name provided"""
    sig = signature(func)
    for i, param in enumerate(sig.parameters.values()):
        if param.name == name:
            return args[i]
    return None


class Activator:
    """
    The Activator class comes with handy default configurations for detecting what messages should be passed along to your bot / a Swarm, and which ones should be ignored. It's just syntactic sugar that allows you to dodge "if: if: if:" bullshit, which to me, looks ugly.

    It's usually used as a decorator, or as a component in a Pattern. But you can use it however you like. If you're just making an Agent and don't want to get into the nitty-gritty, most of the logic is already handled for you by the Agent class – so probably just ignore this.

    It has three default initialisation options:
        on_ping:
            This activates your bot when someone pings it by name (i.e "@Ziggy") or replies to it via the reply button.
        on_topic:
            This activates your bot when a certain topic is mentioned.
        on_diceroll:
            This activates your bot randomly. A good value for this is 400 to 500. Rarity is delightful.

    Example:
        activator = Activator()

        @bot.listen('on_message')
        @activator.check("on_ping", name="Ziggy")
        @activator.check("on_topic", topic="Zig programming")
        @activator.check("on_diceroll", sides=400)
        @swarm.sender("filtered_messages")
        async def send_to_the_swarm(msg: discord.Message) -> discord.Message:
            return msg

    In this case, it would be kinda pointless but this is just a simple demonstration. With this configuration, your bot would talk if
        1) Someone typed "@Ziggy" or "@ziggy"
        2) Someone mentioned the Zig programming language
        3) If a randomly-rolled virtual die with 400 sides landed on 1.

    You can also pass a predicate / a function that returns either True or False, along with some types that it should be called for. For instance, if you have:

        @activator.check(
            checker=lambda article: "AI" in article.headline,
            mandatory=True
        )
        async def receive_news() -> AsyncGenerator[Article, None]:
            ...

    You can stack Activator decorators, but if you do that, you need to be careful about what order you do them in.

        mandatory=False means "hey, it would be great if this event met the criteria, but it's okay, I'll just pass it up the chain to see if anyone else wants it". It's equivalent to an 'or'.

        mandatory=True means "I'm absolutely certain that nobody is interested in this event, so I'll just discard it". It's equivalent to an 'and'.

    Remember: if you use a decorator, then that check isn't permanently added to the Activator. Otherwise you would be adding checks in one place and then having it inappropriately applied everywhere else. If you want to add a check manually and apply it everywhere, do this:

        no_pips_activator = Activator()
        no_pips_activator.add_check(checker=lambda fruit: fruit.pips == 0, mandatory=True)

        @fruit_fly_swarm.send
        @no_pips_activator.check()
        async def fruit_chooser(fruit_salad: List[Fruit]) -> Fruit:
            random.shuffle(fruit_salad)
            return fruit_salad.pop()

        @fruit_fly_swarm.send
        @no_pips_activator.check()
        async def fruit_tree() -> AsyncGenerator[Fruit, None]:
            fruits = ["bananas", "pears", "apples"]
            while True:
                for fruit in fruits:
                    yield fruit

    Activator has one last method, copy() which just allows you to copy an activator without synchronising changes between the two. You should probably do that instead of creating a whole subclass, but you can subclass Activator if you *really* want to.
    """

    def __init__(self, *args: List[Callable]) -> None:
        """This allows you to pass in mandatory checks"""
        self.mandatory_checks = []
        self.optional_checks = []
        self.wrapped_funcs: Dict[str, Dict[str, Dict[str, List[Callable]]]] = {}
        for arg in args:
            if isinstance(arg, Callable) or hasattr(arg, "__call__"):
                self.add_check(checker=arg)  # type: ignore
            else:
                raise TypeError(
                    f"{arg} is not a callable. According to Python, it's a {type(arg)}"
                )

    def copy(self) -> "Activator":
        """
        This allows you to copy an activator without synchronising changes between the two.
        """
        return copy.deepcopy(self)

    def add_check(
        self,
        condition: Optional[str] = None,
        checker: Optional[Callable] = None,
        name: Optional[str] = None,
        topic: Optional[str] = None,
        ignore_topics: Optional[List[str]] = None,
        sides: Optional[int] = None,
        mandatory: bool = False,
    ) -> None:
        """
        This adds a check to the activator. It looks unusual, but it's elegant so whatever.
        """
        try:
            if condition:
                check = {
                    "on_ping": self.on_ping,
                    "on_topic": self.on_topic,
                    "on_diceroll": self.on_diceroll,
                }[condition](
                    name=name, topic=topic, sides=sides, ignore_topics=ignore_topics
                )
                self.optional_checks.append(check)
                return
        except KeyError:
            raise KeyError(
                f"{condition} is not a valid default checker. But it could be. Go and make a pull request if you really want me to add it."
            )
        # Okay, so at this point, the user definitely didn't ask for a default checker.
        if checker is None:
            raise ValueError(
                "What are you doing?? You need to specify a checker or a default checker."
            )
        # If it's not a coroutine, then turn it into one:
        if not inspect.iscoroutinefunction(checker):

            def coroutine_wrapper(func):
                async def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                return wrapper

            coroutine_wrapper.__name__ = checker.__name__
            checker = coroutine_wrapper(checker)
        if mandatory:
            self.mandatory_checks.append(checker)
        else:
            self.optional_checks.append(checker)

    async def meets_all_conditions(
        self, func: Callable, result: Any, direction: str
    ) -> bool:
        async def always_return_true(*args, **kwargs):
            return True

        ors = [
            f(result)
            for f in self.optional_checks
            + self.wrapped_funcs[func.__name__][direction].get("or", [])
        ]
        if len(ors) == 0:
            meets_or_conditions = True
        else:
            meets_or_conditions = any(
                await asyncio.gather(
                    *[
                        f(result)
                        for f in self.optional_checks
                        + self.wrapped_funcs[func.__name__][direction].get("or", [])
                    ]
                )
            )
        meets_inbuilt_and_conditions = all(
            await asyncio.gather(
                *[
                    f(result)
                    for f in self.mandatory_checks
                    + self.wrapped_funcs[func.__name__][direction].get("and", [])
                    + [always_return_true]
                ]
            )
        )
        logger.debug(
            f"The function: '{func.__name__}'. Does it meet the 'or' conditions? {meets_or_conditions}. Does it meet the 'and' conditions? {meets_inbuilt_and_conditions}"
        )
        if meets_or_conditions and meets_inbuilt_and_conditions:
            logger.debug("I decided that the conditions were met.")
            return True
        else:
            logger.debug("I decided that the conditions were NOT met.")
            return False

    def decorator(
        self,
        func: Callable,
        mandatory: Optional[bool] = None,
        checker: Optional[Callable] = None,
        apply_to_inputs: bool = False,
        apply_to_outputs: bool = False,
        keyword: Optional[str] = None,
    ) -> Callable:
        if not apply_to_inputs and not apply_to_outputs:
            raise ValueError(
                "You need to specify whether you want to apply the decorator to inputs or outputs."
            )
        if apply_to_inputs and not keyword:
            raise ValueError(
                "You need to specify keywords to apply the decorator to, if you're choosing inputs. Otherwise how am I supposed to know what to apply it to?"
            )

        applied_to = {
            True: "inputs",
            False: "outputs",
        }[apply_to_inputs]

        if mandatory and checker:
            category = {
                True: "and",
                False: "or",
            }[mandatory]
            if not func.__name__ in self.wrapped_funcs:
                self.wrapped_funcs[func.__name__] = dict()
                self.wrapped_funcs[func.__name__][applied_to] = dict()
                self.wrapped_funcs[func.__name__][applied_to][category] = []
            self.wrapped_funcs[func.__name__][applied_to][category].append(checker)
        elif func.__name__ not in self.wrapped_funcs:
            self.wrapped_funcs[func.__name__] = dict()
            self.wrapped_funcs[func.__name__][applied_to] = dict()
            self.wrapped_funcs[func.__name__][applied_to]["and"] = []
            self.wrapped_funcs[func.__name__][applied_to]["or"] = []

        async def async_generator_inner(*args, **kwargs) -> Any:
            if apply_to_inputs and (kwargs or args) and keyword:
                try:
                    kw = kwargs[keyword]
                except KeyError:
                    kw = get_arg_by_name(keyword, args, func)
                if await self.meets_all_conditions(func, kw, applied_to):
                    pass
                else:
                    raise StopAsyncIteration
            async for result in func(*args, **kwargs):
                if apply_to_outputs:
                    yield await self.meets_all_conditions(func, result, applied_to)
                else:
                    yield result

        async def generator_inner(*args, **kwargs) -> Any:
            if apply_to_inputs and (kwargs or args) and keyword:
                try:
                    kw = kwargs[keyword]
                except KeyError:
                    kw = get_arg_by_name(keyword, args, func)
                if await self.meets_all_conditions(func, kw, applied_to):
                    pass
                else:
                    raise StopIteration
            for result in func(*args, **kwargs):
                if apply_to_outputs:
                    yield await self.meets_all_conditions(func, result, applied_to)
                else:
                    yield result

        async def awaitable_inner(*args, **kwargs) -> Any:
            if apply_to_inputs and (kwargs or args) and keyword:
                try:
                    kw = kwargs[keyword]
                except KeyError:
                    kw = get_arg_by_name(keyword, args, func)
                if await self.meets_all_conditions(func, kw, applied_to):
                    pass
                else:
                    return None
            result = await func(*args, **kwargs)
            if apply_to_outputs:
                if await self.meets_all_conditions(func, result, applied_to):
                    return result
                else:
                    return None
            else:
                return result

        async def sync_inner(*args, **kwargs) -> Any:
            if apply_to_inputs and (kwargs or args) and keyword:
                try:
                    kw = kwargs[keyword]
                except KeyError:
                    kw = get_arg_by_name(keyword, args, func)
                if await self.meets_all_conditions(func, kw, applied_to):
                    pass
                else:
                    return None
            else:
                logger.debug(
                    f"{func.__name__} is not a coroutine. I'm going to run it synchronously. Was it called with apply_to_inputs? {apply_to_inputs}. Was it called with kwargs? {kwargs}. Was a keyword provided? {keyword}"
                )
            result = func(*args, **kwargs)
            if apply_to_outputs:
                if await self.meets_all_conditions(func, result, applied_to):
                    return result
                else:
                    return None
            else:
                return result

        # Return the appropriate inner decorator based on the function's type
        # Log the type first using inspect
        # logger.debug(f"Is {func.__name__} is a coroutine function? {inspect.iscoroutinefunction(func)}. Is it a generator? {inspect.isgeneratorfunction(func)}. Is it an async generator? {inspect.isasyncgenfunction(func)}")
        if inspect.isasyncgenfunction(func):
            return async_generator_inner
        elif inspect.isgeneratorfunction(func):
            return generator_inner
        elif inspect.iscoroutinefunction(func):
            return awaitable_inner
        else:
            return sync_inner

    @classmethod
    def check_once(
        cls,
        checker: Optional[Callable] = None,
        mandatory: bool = True,
        outputs: bool = False,
        inputs: bool = False,
        keyword: Optional[str] = None,
    ) -> Callable:
        """
        This is a metadecorator that allows you to make non-permanent checks on a case-by-case basis to whatever event-listener you want.
        """

        if checker and not inspect.iscoroutinefunction(checker):
            # If it's not a coroutine, then turn it into one.
            def coroutine_wrapper(func):
                async def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                return wrapper

            coroutine_wrapper.__name__ = checker.__name__
            checker = coroutine_wrapper(checker)
        if checker:
            instance = cls()
            instance.add_check(checker=checker, mandatory=mandatory)

        def decorator(func: Callable) -> Callable:
            return instance.decorator(
                func=func,
                mandatory=mandatory,
                checker=checker,
                apply_to_inputs=inputs,
                apply_to_outputs=outputs,
                keyword=keyword,
            )

        return decorator

    def check(
        self,
        checker: Optional[Callable] = None,
        mandatory: bool = False,
        outputs: bool = False,
        inputs: bool = False,
        keyword: Optional[str] = None,
    ) -> Callable:
        """
        This is a metadecorator that allows you to make non-permanent checks on a case-by-case basis to whatever event-listener you want.
        """

        if checker and not inspect.iscoroutinefunction(checker):
            # If it's not a coroutine, then turn it into one.
            def coroutine_wrapper(func):
                async def wrapper(*args, **kwargs):
                    return func(*args, **kwargs)

                return wrapper

            coroutine_wrapper.__name__ = checker.__name__
            checker = coroutine_wrapper(checker)

        def decorator(func: Callable) -> Callable:
            return self.decorator(
                func=func,
                mandatory=mandatory,
                checker=checker,
                apply_to_inputs=inputs,
                apply_to_outputs=outputs,
                keyword=keyword,
            )

        return decorator

    def on_ping(self, name: str, **kwargs) -> Callable:
        """
        This activates your bot when someone pings it by name (i.e "@Ziggy") or replies to it via the reply button.
        """

        async def checker(msg: discord.Message) -> bool:
            if f"@{name.lower()}" in msg.content.lower():
                return True
            if msg.embeds and msg.embeds[0].author.name == name:
                return True
            try:
                if msg.reference.resolved.author.name == name:  # type: ignore
                    return True
                else:
                    return False
            except AttributeError:
                return False
            return False

        return checker

    def on_topic(self, topic: str, ignore_topics: List[str], **kwargs) -> Callable:
        ranker = Ranker()
        on_topic = (
            f"This sentence is specifically related to {topic} and mentions {topic}"
        )
        not_on_topic = [
            "This sentence is unoffensive and contains no upsetting content",
            "This sentence is calm and factual",
            "This sentence is conversational and casual",
            "This sentence is not very interesting and talks about generic topics",
            "This sentence is about science, sports, art, computers, or music",
        ]
        topics = [on_topic]
        topics.extend(not_on_topic)
        if ignore_topics:
            topics.extend(
                [
                    f"This sentence is specifically related to {topic} and mentions {topic}"
                    for topic in ignore_topics
                ]
            )

        async def checker(msg: discord.Message) -> bool:
            content = msg.content
            top_topic = await ranker.rank(
                texts=tuple(topics),
                query=content,
                top_k=1,
                model=ranker.default_model,
                return_none_if_below_threshold=True,
                threshold=0.3,
            )

            if top_topic:
                if top_topic[0] == on_topic:
                    return True
                else:
                    return False
            return False

        return checker

    def on_diceroll(self, sides: int, **kwargs) -> Callable:
        """
        This activates your bot randomly. A good value for this is 400 to 500. Rarity is delightful.
        """

        async def checker(msg: discord.Message) -> bool:
            return random.randint(1, sides) == 1

        return checker
