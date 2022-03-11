
# optional: uvloop makes stuff go around 3-4 times faster
#import uvloop
#uvloop.install()
import regex as re
import discord
import asyncio
from typing import Callable, Optional

AGENT_PREFIX = "&"

async def discord_to_irc(msg: discord.Message):
    # Replace substrings matching the pattern "<:word:id>" with an empty string
    content = re.sub(r"<:[a-zA-Z0-9_]+:[0-9]+>", "", msg.content)
    if not hasattr(msg.author, "nick") or not msg.author.nick: #type: ignore
        name_to_iterate_over = msg.author.name
    else:
        name_to_iterate_over = msg.author.nick #type: ignore
    name = "".join([c for c in name_to_iterate_over if c.isascii()])
    return f"<{name}> {content}"

async def get_reference_for_message(
    message: discord.Message,
) -> Optional[discord.Message]:
    # This first part allows personas to talk to one another, which is incredibly funny. Disable it if you don't have a sense of humour / don't have enough API keys.
    try:
        reply_to = int(str(message.embeds[0].footer.text))
        msg = await message.channel.fetch_message(reply_to)
        return msg
    except (AttributeError, IndexError):
        if message.reference and isinstance(
            message.reference.resolved, discord.Message
        ):
            return message.reference.resolved
        else:
            return None

async def get_conversation_history(
    message: discord.Message, maximum_chars: int = 800
) -> list[str]:
    # Set maximum_chars higher if you are an exorbitant glutton with tokens to spare
    messages = []
    messages.append(await discord_to_irc(message))
    while True:
        msg = await get_reference_for_message(message)
        if msg is None:
            break
        messages.append(await discord_to_irc(msg))
        message = msg
        if len("".join(messages)) > maximum_chars:
            break
    messages.reverse()
    return messages

async def check_if_message_refers_to_name(name: str, message: discord.Message) -> bool:
    if f"{AGENT_PREFIX}{name.lower()}" in message.content.lower():
        return True
    msg = await get_reference_for_message(message)
    if msg and msg.author.name == name:
        return True
    return False
    # Fuck around with this if you want your agents to respond to other things

def embed_from_msg(msg: discord.Message):
    if msg.author.avatar:
        avatar = msg.author.avatar.url
    else:
        avatar = "https://www.google.com/nothing.png"
    author_name = msg.author.name
    contents = msg.content
    embed = discord.Embed(description=contents)
    embed.set_author(name=author_name, icon_url=avatar)
    embed.set_footer(text=f"{msg.id}")
    return embed
    # This adds an embed to discord messages which allows Agents to figure out who the hell they were replying to. It's an alternative to using Memory

from personate.face.face2 import Face
from acrossword import Ranker

class Agent:
    def __init__(
        self,
        bot: discord.Bot,
        name: str,
        avatar_url: str,
        description: str,
        is_ai: bool = False,
        loading_message: str = "...",
        **kwargs
    ):
        self.name = name
        self.description = description
        self.avatar_url = avatar_url
        self.is_ai = is_ai
        self.facts = set()
        self.examples = set()
        self.face = Face(
            bot=bot,
            avatar_url=self.avatar_url,
            username=self.name,
            loading_message=loading_message,
        )
        self.ranker = Ranker()

    def add_examples(self, examples: list):
        self.examples.update(set(examples))

    def add_example(self, example: str):
        self.examples.add(example)

    def add_facts(self, facts: list):
        self.facts.update(set(facts))

    def add_fact(self, fact: str):
        self.facts.add(fact)

    def facts_as_str(self, facts) -> str:
        return "- " + "\n- ".join(facts)

    async def rerank_examples(self, query: str, max_chars: int = 710) -> list[str]:
        try:
            _top_results = await self.ranker.rank(texts=tuple(self.examples), query=query, top_k=len(self.examples), model=self.ranker.default_model)
        except Exception as e:
            print(e)
            return []
        top_results = []
        for res in _top_results:
            top_results.append(res)
            if len(''.join(top_results)) > max_chars:
                break
        return top_results

    async def rerank_facts(self, query: str, max_chars: int = 180) -> str:
        try:
            _top_results = await self.ranker.rank(texts=tuple(self.facts), query=query, top_k=len(self.facts), model=self.ranker.default_model)
        except Exception as e:
            print(e)
            return ""
        top_results = []
        for res in _top_results:
            top_results.append(res)
            if len(''.join(top_results)) > max_chars:
                break
        return self.facts_as_str(top_results)

    def __repr__(self):
        return f"Agent({self.name})"
    # A lot of reduplicated code here

class AgentRouter:
    def __init__(self, bot: discord.Bot, dialogue_generator: Callable):
        self.bot = bot
        self.agents: dict[str, Agent] = {}
        self.dialogue_generator = dialogue_generator

    async def check_if_refers_to_agent(self, msg: discord.Message):
        for name, agent in self.agents.items():
            if await check_if_message_refers_to_name(name, msg):
                yield agent

    async def generate_agent_responses(self, msg: discord.Message):
        async for agent in self.check_if_refers_to_agent(msg):
            asyncio.create_task(self.generate_agent_response(agent, msg))

    async def generate_agent_response(self, agent: Agent, msg: discord.Message):
        if not agent:
            return
        agent_message = await agent.face.send_loading(msg.channel.id)
        conversation = "\n".join(await get_conversation_history(msg))

        conversation = conversation.replace(f"{AGENT_PREFIX}{agent.name}", "")
        conversation = conversation.replace(f"{AGENT_PREFIX}{agent.name.lower()}", "")

        examples = await agent.rerank_examples(conversation[-120:])
        facts = await agent.rerank_facts(conversation[-120:])
        
        reply = await self.dialogue_generator(
            name=agent.name,
            description=agent.description,
            conversation=conversation,
            is_ai=agent.is_ai,
            examples=examples,
            facts=facts,
        )
        
        await agent_message.update(content=reply, embed=embed_from_msg(msg))

    def add_agent(self, agent: Agent):
        self.agents[agent.name] = agent
