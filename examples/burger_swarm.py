import enum
from enum import auto
from typing import Any, AsyncGenerator, List, Type


class Bun(enum.Enum):
    """
    Enum of all possible buns
    """

    WHOLEGRAIN = auto()
    WHITE = auto()
    SESAME_SEEDS = auto()

    def __init__(self, is_keto: bool = False):
        self.has_seeds = False

    async def add_sesame_seeds(self) -> None:
        #await asyncio.sleep(0.3)
        self.has_seeds = True

    def __repr__(self):
        if self.has_seeds:
            return f"{self.name} with sesame seeds"
        return f"{self.name}"


class Pattie(enum.Enum):
    """
    Enum of all possible patties
    """

    CHICKEN = auto()
    BEEF = auto()
    PORK = auto()
    VEGAN = auto()

    def __init__(self, cooked: bool = False):
        self.cooked = False

    async def cook(self) -> None:
        #await asyncio.sleep(1.5)
        self.cooked = True

    def __repr__(self):
        if self.cooked:
            return f"{self.name} cooked"
        return f"{self.name}"


class Vegetables(enum.Enum):
    """
    Enum of all possible vegetables
    """

    TOMATO = auto()
    ONION = auto()
    LETTUCE = auto()
    PICKLES = auto()
    MUSHROOMS = auto()
    PEPPERS = auto()
    SPINACH = auto()

    def __init__(self, has_mayo: bool = False):
        self.has_mayo = False

    async def add_mayo(self) -> None:
        #await asyncio.sleep(0.5)
        self.has_mayo = True

    def __repr__(self):
        if self.has_mayo:
            return f"{self.name} with mayo"
        return f"{self.name}"


class Burger:
    def __init__(
        self,
        customer_name: str,
        price: float,
        buns: list,
        patties: list,
        vegetables: list,
        mayo: bool = False,
        sesame_seeds: bool = False,
    ):
        self.customer_name = customer_name
        self.price = price
        self.finished = False
        self.contents: set = set()
        self.buns: List[Bun] = buns
        self.patties: List[Pattie] = patties
        self.vegetables: List[Vegetables] = vegetables
        self.mayo = mayo
        self.sesame_seeds = sesame_seeds

    def __contains__(self, item):
        return item in self.contents

    async def add_item(self, item: Any):
        #await asyncio.sleep(0.5)
        self.contents.add(item)

    # convenience function that tells us if self.contents contains a type of item
    def has(self, item: Type) -> bool:
        return len([i for i in self.contents if isinstance(i, item)]) > 0

    # the same as the above, but for multiple types
    def has_any(self, *items: Type) -> bool:
        return (
            len(
                [i for i in self.contents if any(isinstance(i, item) for item in items)]
            )
            > 0
        )

    def __repr__(self):
        return f"<Burger customer={self.customer_name} price={self.price} contents={self.contents}>"


from threading import Lock


class Till:
    dollars = 0
    burgers_sold = 0
    _lock = Lock()

    @classmethod
    async def add_dollars(cls, dollars: float):
        with cls._lock:
            cls.dollars += dollars

    @classmethod
    async def add_burger(cls):
        with cls._lock:
            cls.burgers_sold += 1


from swarm.swarm_fork import Swarm
import random
import asyncio

swarm = Swarm(name="makes burgers")


async def generate_random_order():
    buns = [Bun.WHOLEGRAIN, Bun.WHITE, Bun.SESAME_SEEDS]
    patties = [Pattie.CHICKEN, Pattie.BEEF, Pattie.PORK, Pattie.VEGAN]
    vegetables = [
        Vegetables.TOMATO,
        Vegetables.ONION,
        Vegetables.LETTUCE,
        Vegetables.PICKLES,
        Vegetables.MUSHROOMS,
        Vegetables.PEPPERS,
        Vegetables.SPINACH,
    ]
    burger = Burger(
        customer_name=f"Customer {random.randint(0, 10000)}",
        price=random.randint(10, 20),
        buns=random.sample(buns, random.randint(1, 2)),
        patties=random.sample(patties, random.randint(1, 3)),
        vegetables=random.sample(vegetables, random.randint(1, 3)),
        mayo=random.choice([True, False]),
        sesame_seeds=random.choice([True, False]),
    )
    return burger


from utils.logger import logger


class Coupon(enum.Enum):
    """
    Enum of all possible coupons
    """

    HALF_PRICE = auto()
    FREE = auto()
    NO_COUPON = auto()


# Generate a bunch of random orders + coupons
@swarm.send
async def open_burger_stand(minutes: int):
    for m in range(minutes):
        # if random.choice([True, False, True]):
        yield await generate_random_order(), 0
        # One in 20 burgers are free, one in 10 are half price
        if random.choice(range(20)) == 0:
            yield Coupon.FREE
        elif random.choice(range(10)) == 0:
            yield Coupon.HALF_PRICE
        else:
            yield Coupon.NO_COUPON


# Collect finalised burgers and send money to the till
# This is a normal generator function, still works, still doesn't block the event-loop
@swarm.send
@swarm.collect({"burger": (Burger, 4, lambda b: b.finished)})
def serve_finished_burgers(burger: Burger):
    logger.info(
        f"{burger.customer_name} has received their burger. The burger cost ${burger.price}. The burger was: {burger}"
    )
    yield burger.price * 1.15, "price"
    # Randomly generate a tip amount
    yield random.randint(0, 10), "tip"


# Add money to the till
@swarm.collect(
    {"money": (float, "price", lambda p: p.data > 0), "coupon": (Coupon, None, None)}
)
async def add_money_to_till(money: float, coupon: Coupon):
    if coupon == Coupon.HALF_PRICE:
        money /= 2
    elif coupon == Coupon.FREE:
        money = 0
    await asyncio.sleep(0.2)
    await Till.add_dollars(money)
    await Till.add_burger()
    logger.info(f"Added ${money} to the till, your coupon was {coupon}")


# Collect tips
@swarm.collect({"tip": (int, "tip", lambda t: t.data > 0)})
async def add_tip_to_till(tip: float):
    await Till.add_dollars(tip)
    logger.info(f"Woho! We got a tip! Added ${tip} to the till")


# Add vegetables to the burger
# Ordinary async func, not a generator
@swarm.send
@swarm.collect(
    {
        "burger": (Burger, 2, lambda b: not b.finished),
    }
)
async def add_vegetables_to_burger(burger: Burger):
    desired_vegetables = burger.vegetables
    for v in desired_vegetables:
        if burger.mayo:
            await v.add_mayo()
        await burger.add_item(v)
    logger.info(f"Added {burger.vegetables} to {burger}")
    return burger, 3


# Cook patties and add them to the burger
@swarm.send
@swarm.collect(
    {
        "burger": (Burger, 1, lambda b: not b.finished),
    }
)
async def cook_patties(burger: Burger):
    desired_patties = burger.patties
    for p in desired_patties:
        await p.cook()
        await burger.add_item(p)
    logger.info(f"Cooked {burger.patties} and added them to {burger}")
    return burger, 2


# Add buns to the burger
@swarm.send
@swarm.collect(
    {
        "burger": (Burger, 0, lambda b: not b.finished),
    }
)
async def add_buns(burger: Burger):
    desired_buns = burger.buns
    for b in desired_buns:
        if burger.sesame_seeds:
            await b.add_sesame_seeds()
        await burger.add_item(b)
    logger.info(f"Added {burger.buns} to {burger}")
    return burger, 1


# Check the burgers for their finishedness, and if they are, then mark them as finished
# Implemented as a synchronous func with a time.sleep of 2, just to test whether it can be threaded properly.
@swarm.send
@swarm.collect(
    {
        "burger": (Burger, 3, lambda b: not b.finished),
    }
)
def mark_burger_as_finished(burger: Burger):
    buns, patties, vegetables = (
        set(burger.buns),
        set(burger.patties),
        set(burger.vegetables),
    )
    current_contents: set = burger.contents
    logger.info(
        f"The current contents are {current_contents}, the desired contents are {buns, patties, vegetables}"
    )
    if (
        buns.issubset(current_contents)
        and patties.issubset(current_contents)
        and vegetables.issubset(current_contents)
    ):
        burger.finished = True
        logger.info(f"{burger} is finished")
        import time
        time.sleep(2)
        return burger, 4


async def main():
    async for order in open_burger_stand(10):
        pass
    await asyncio.sleep(12)
    # So we can see the final state of the system


asyncio.run(main())
