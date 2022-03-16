
# optional: uvloop makes stuff go around 3-4 times faster
#import uvloop
#uvloop.install()
import random
import regex as re
import discord
import json
import asyncio
from typing import Callable, Dict, Optional, Union, List, Set
import inspect

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

class UpdateableMessageWrapper:
    '''This contains a discord.WebhookMessage or a discord.Message object, and has a method for updating its content, by passing down the kwargs from the call.'''
    def __init__(self, message: discord.Message):
        self.message = message
    async def update(self, **kwargs):
        return await self.message.edit(**kwargs)

class Face:
    """
    This is maybe one of the simplest classes in the library. It manages webhooks and posts as the webhook with a specific appearance (avatar_url and username).
    """

    def __init__(
        self,
        bot: discord.Bot,
        avatar_url: str,
        username: str,
        loading_message: Optional[Union[List[str], str]] = None,
    ):
        self.bot = bot
        self.avatar_url = avatar_url
        self.username = username
        self.loading_message = loading_message
        self.webhooks: Dict[int, discord.Webhook] = {}


    async def get_webhook(self, channel_id: int) -> Optional[discord.Webhook]:
        channel = self.bot.get_channel(channel_id)
        if isinstance(channel, discord.TextChannel):

            def predicate(webhook: discord.Webhook):
                return webhook.user == self.bot.user

            webhooks: List[discord.Webhook] = await channel.webhooks()
            webhook = discord.utils.find(lambda m: predicate(m), webhooks)
            if not webhook:
                if self.bot.user:
                    try:
                        webhook = await channel.create_webhook(name=self.bot.user.name)
                    except discord.HTTPException:
                        pass
            if webhook:
                return webhook
        return None

    async def send_custom(
        self,
        channel_id: int,
        content: str,
        avatar_url: str,
        username: str,
        **kwargs,
    ) -> UpdateableMessageWrapper:
        """Flexible method that handles different cases."""
        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel) or not channel:
            raise ValueError(
                f"Channel: {channel_id} is not a valid text channel. Please provide a valid text channel id."
            )
        webhook = await self.get_webhook(channel.id)
        if webhook:
            message = await webhook.send(
                content=content,
                avatar_url=avatar_url,
                username=username,
                wait=True,
                **kwargs,
            )
        else:
            message = await channel.send(content, **kwargs)
        return UpdateableMessageWrapper(message)

    async def send_loading(self, channel_id: int) -> UpdateableMessageWrapper:
        if not self.loading_message:
            self.loading_message = "...thinking..."
        if isinstance(self.loading_message, str):
            loading_message = self.loading_message
        else:
            loading_message = random.choice(self.loading_message)
        return await self.send_custom(
            channel_id, loading_message, self.avatar_url, self.username
        )

    async def send(self, channel_id: int, content: str, **kwargs) -> UpdateableMessageWrapper:
        return await self.send_custom(
            channel_id, content, self.avatar_url, self.username, **kwargs
        )

class Agent:
    def __init__(
        self,
        bot: discord.Bot,
        name: str,
        avatar: str,
        introduction: str,
        is_ai: bool = False,
        loading_message: str = "...",
        **kwargs
    ):
        self.name = name
        self.description = introduction
        self.avatar_url = avatar
        self.is_ai = is_ai
        self.facts = set()
        self.response_type = None
        self.annotation = None
        self.examples = set()
        self.messages_cache: dict = {}
        self.post_translators: List[Callable] = []
        self.face = Face(
            bot=bot,
            avatar_url=self.avatar_url,
            username=self.name,
            loading_message=loading_message,
        )
        self.ranker = None

    @classmethod
    def from_json(cls, filename: str, bot: discord.Bot) -> "Agent":
        with open(filename, "r") as f:
            data = json.load(f)
        agent = cls(**data, is_ai=True, bot=bot)
        agent.examples = set()
        for example in data["examples"]:
            try:
                agent_dialogue = example.pop("agent")
                user = list(example.keys())[0]
                final_example = f"""<{user}> {example[user]}\n<{agent.name}> {agent_dialogue}"""
                print(final_example)
                agent.add_example(final_example)
            except:
                pass
        return agent

    def set_response_type(self, response_type: str):
        self.response_type = response_type

    def set_annotation(self, annotation: str):
        self.annotation = annotation

    def add_examples(self, examples: list):
        self.examples.update(set(examples))

    def add_ranker(self, ranker):
        self.ranker = ranker

    def add_example(self, example: str):
        self.examples.add(example)

    def add_facts(self, facts: list):
        self.facts.update(set(facts))

    def add_fact(self, fact: str):
        self.facts.add(fact)

    def add_post_translator(self, translator: Callable):
        self.post_translators.append(translator)

    async def translate(self, response: str):
        original_response = response
        for translator in self.post_translators:
            if inspect.iscoroutinefunction(translator):
                response = await translator(response)
            else:
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(None, translator, response)
        self.messages_cache[response] = original_response
        return response

    def facts_as_str(self, facts) -> Optional[str]:
        if not facts:
            return None
        return "- " + "\n- ".join(facts)

    async def rerank_examples(self, query: str, max_chars: int = 710) -> list[str]:
        if not self.ranker:
            return []
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

    async def rerank_facts(self, query: str, max_chars: int = 180) -> Optional[str]:
        if not self.ranker:
            return ""
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
        if agent.ranker:
            examples = await agent.rerank_examples(conversation[-120:])
            facts = await agent.rerank_facts(conversation[-120:])
        else:
            examples = None
            facts = None

        reply = await self.dialogue_generator(
            name=agent.name,
            description=agent.description,
            conversation=conversation,
            is_ai=agent.is_ai,
            examples=examples,
            facts=facts,
            response_type=agent.response_type,
            annotation=agent.annotation,
        )

        reply = await agent.translate(reply)
        
        await agent_message.update(content=reply, embed=embed_from_msg(msg))

    def add_agent(self, agent: Agent):
        self.agents[agent.name] = agent
