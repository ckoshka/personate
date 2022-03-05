from abc import ABC, abstractmethod, abstractproperty
from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Union,
    Tuple,
    Coroutine,
    Callable,
    Generator,
)
import inspect
import asyncio
from rapidfuzz import fuzz, process
import functools
from personate.utils.logger import logger


class Condition(ABC):
    def __init__(self, condition: Callable) -> None:
        self.condition = condition

    async def validate(self, *args, **kwargs) -> bool:
        loop = asyncio.get_event_loop()
        if inspect.iscoroutinefunction(self.condition):
            return await self.condition(*args, **kwargs)
        else:
            return await loop.run_in_executor(
                None, functools.partial(self.condition, *args, **kwargs)
            )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.condition.__name__})"


class Filter(ABC):
    def __init__(self, filters: List[Union["Filter", "Condition"]], **kwargs) -> None:
        self.conditions: List[Union[Condition, Filter]] = filters

    def __repr__(self) -> str:
        return f"<Filter {self.conditions}>"

    async def validate(self, *args, **kwargs) -> bool:
        bools = [
            await condition.validate(*args, **kwargs) for condition in self.conditions
        ]
        names = [condition for condition in self.conditions]
        bools_and_names = "\n".join(
            f"{name}: {bool_}" for name, bool_ in zip(names, bools)
        )
        logger.debug(f"{self} produced the following results: {bools_and_names}")

        return any(bools)

    @classmethod
    def redo(cls, redos: int = 3, **kwargs) -> Callable:
        instance = cls(**kwargs)

        def wrapper(func: Callable) -> Callable:
            async def inner_wrapper(*args, **kwargs) -> Any:
                for _ in range(redos):
                    try:
                        res = await func(*args, **kwargs)
                        if await instance.validate(res):
                            return res
                    except Exception as e:
                        print(f"{e}")
                return await func(*args, **kwargs)

            return inner_wrapper

        return wrapper

    def add_condition(self, condition: Union[Condition, "Filter"]) -> None:
        self.conditions.append(condition)


class DeviatesFromScriptFilter(Filter):
    def __init__(self, required_formatting: str = "\n<") -> None:
        async def does_not_contain_formatting(response: str, **kwargs) -> bool:
            return required_formatting not in response

        DeviatesFromScriptCondition = Condition(does_not_contain_formatting)
        super().__init__([DeviatesFromScriptCondition])


async def too_similar(threshold: int, response: str, final_prompt: str) -> bool:
    response = response.split("\n<")[0]
    return fuzz.partial_token_sort_ratio(response, final_prompt) >= threshold  # type: ignore


class TooSimilarFilter(Filter):
    def __init__(self, threshold: int = 68) -> None:
        self.threshold = threshold
        super().__init__([Condition(too_similar)])

    async def validate(self, response: str, final_prompt: str, **kwargs) -> bool:
        return await super().validate(
            response=response, final_prompt=final_prompt, threshold=self.threshold
        )


# from decos.slurslist import slurs
async def contains_slurs(slurs: Set[str], response: str, **kwargs) -> bool:
    words = set(response.lower().split())
    common_words = words.intersection(slurs)
    return len(common_words) > 0


class SlurFilter(Filter):
    def __init__(self, slurs: Optional[List[str]] = None) -> None:
        if not slurs:
            slurs = get_inbuilt_slurs()
        self.slurs = set(slurs)
        super().__init__([Condition(contains_slurs)])

    async def validate(self, response: str, **kwargs) -> bool:
        return await super().validate(response=response, slurs=self.slurs)


import csv


def get_inbuilt_slurs() -> List[str]:
    slurs: str = __import__("personate.decos.slurs", fromlist=["slurs"]).slurs
    reader = csv.reader(slurs.splitlines())
    return [row[0] for row in reader if not "Mild" in row[-1]]


class DefaultFilter(Filter):
    """This simply contains DeviatesFromScriptFilter and is used as the default filter, but I'll add more stuff to it later."""

    def __init__(self) -> None:
        super().__init__([DeviatesFromScriptFilter(), TooSimilarFilter(), SlurFilter()])
