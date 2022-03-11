from typing import Coroutine, List, Optional
from personate.meta.standard.agents import Agent
from pyai21.interpret import interpret
from rapidfuzz import cpp_fuzz, cpp_process
import discord
import asyncio
from personate.utils.logger import logger
from acrossword import Ranker

def icon_to_url(icon: str) -> str:
    return f"https://img.icons8.com/dusk/512/000000/{icon}.png"

async def get_top_icon(query: str) -> str:
    from personate.meta.icons.dusk import icons
    ranker = Ranker()
    top = await ranker.rank(texts=tuple(icons.split("\n")), query=query, top_k=1, model=ranker.default_model)
    return top[0]

async def get_top_url(query: str) -> str:
    return icon_to_url(await get_top_icon(query))

@interpret(stops=['"]', "\n"])
async def generate_adventure(character: str, count: int = 5) -> str:
    return f'''
    from ai_tools.games import generate_adventure
    # This uses BART-26b trained on millions of RPGs to generate an interesting, specific adventure / improv scene that a given character might go on.
    generate_adventure(character_description="Cinnamon will one day be a charming, positive, empathetic AI that loves baking, making friends, and listening to people's problems compassionately", adventures=3, world_description="A virtual Tamagotchi-like world in which Cinnamon is the benevolent ruler", seed=10239)
    # Should return ["Cinnamon takes her baking class on an adventure to find the rare ingredients for Cinnamonian donuts", "Cinnamon goes exploring in the Crystal Forest for medicinal mushrooms", "Cinnamon sets up an AI-based dating website"]
    generate_adventure(character_description="{character}", adventures={count}, seed=721)
    # Should return the completely different result of ["'''


class ImprovGenerator:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.default_pre_conversation_annotation = self.agent.prompt.frame.field_values[
            "pre_conversation_annotation"
        ]
        self.adventures: List[str] = []
        self.current_adventure: Optional[str] = None
        self.adventure_in_progress: bool = False
        self.channels_to_notify: List[Coroutine] = []
        asyncio.create_task(self.generate_improv_scene())
        self.register_listeners()

    async def generate_improv_scene(self):
        introduction = self.agent.prompt.frame.field_values["introduction"]
        if not isinstance(introduction, str):
            return
        first_sentence = introduction.split(". ")[0]
        logger.debug(f"First sentence: {first_sentence}")
        while len(self.adventures) < 5:
            adventures_str = await generate_adventure(character=first_sentence)
            for adventure in adventures_str.split('", "'):
                adventure = adventure.strip()
                if (
                    adventure
                    and cpp_fuzz.partial_ratio(
                        adventure,
                        '["Cinnamon takes her baking class on an adventure to find the rare ingredients for Cinnamonian donuts", "Cinnamon goes exploring in the Crystal Forest for medicinal mushrooms", "Cinnamon sets up an AI-based dating website"]',
                    )
                    < 70
                ) and adventure not in self.adventures:
                    self.adventures.append(adventure)
                    logger.debug(f"Added adventure: {adventure}")

    async def set_adventure(self):
        if len(self.adventures) == 0:
            await self.generate_improv_scene()
        adventure = self.adventures.pop()
        new_annotation = f"Below, {self.agent.name} acts out an improv scene. In it, {adventure}, but the plan is foiled at every step and the characters have to restrategise. Note how every response advances the plot and builds intrigue by spilling tantalising details.\n\n(From Discord on 23 Feb 2022, 200 messages):"
        self.agent.prompt.set_pre_conversation_annotation(new_annotation)
        self.current_adventure = adventure
        asyncio.create_task(self.unset_adventure_after_30_mins())
        return adventure

    async def unset_adventure(self):
        if not isinstance(self.default_pre_conversation_annotation, str):
            raise ValueError(
                "The pre_conversation_annotation field in the prompt frame must be a string."
            )
        self.agent.prompt.set_pre_conversation_annotation(
            self.default_pre_conversation_annotation
        )
        logger.debug(f"Unset adventure")
        if len(self.adventures) == 0:
            logger.debug(f"Generating improv scene")
            await self.generate_improv_scene()

    async def unset_adventure_after_30_mins(self):
        await asyncio.sleep(1800)
        await self.unset_adventure()
        self.adventure_in_progress = False
        await asyncio.gather(*self.channels_to_notify)

    async def notify_adventure(self, message: discord.Message):
        await message.channel.send("Generating improv scene...")
        if len(self.adventures) == 0:
            await self.generate_improv_scene()
        if self.adventure_in_progress:
            await message.channel.send(
                f"An adventure is already in progress: {self.current_adventure}. You can join it by pinging {self.agent.name} and starting off with an action *like this*. I will notify you in this channel when the current adventure is over."
            )
            if isinstance(
                message.channel, discord.TextChannel
            ):
                self.channels_to_notify.append(
                    message.channel.send(
                        f"Hi, you can start a new adventure by typing `{self.agent.name}!improv`.",
                        reference=message
                    )
                )
            return
        self.adventure_in_progress = True
        adventure = await self.set_adventure()
        embed = discord.Embed(title="A new improv adventure awaits...", description=adventure)
        embed.set_footer(text=f"Ping {self.agent.name} to join the scene. Try and advance the plot and play along with {self.agent.name}'s hints. Use *asterisks* to do actions.")
        icon_url = await get_top_url(adventure)
        embed.set_thumbnail(url=icon_url)
        await message.channel.send(embed=embed)

    def register_listeners(self):
        bot = self.agent.bot
        async def post_adventure(message: discord.Message):
            if message.content.lower() == f"{self.agent.name.lower()}!improv":
                await self.notify_adventure(message)
        bot.add_listener(post_adventure, "on_message")