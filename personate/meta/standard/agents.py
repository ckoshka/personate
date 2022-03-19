# TODO: send messages internally if they contain @system, don't show them to the end-user.
from typing import AsyncGenerator, Callable, Coroutine, Dict, List, Optional, Union

import discord
import ujson as json
import uvloop
from acrossword import Document, DocumentCollection, Ranker
from personate.activators.activators import Activator
from asynchronise import Asynchronise
from personate.decos.filter import Filter
from personate.decos.translators.translator import (
    DiscordResponseTranslator,
    EmptyTranslator,
    MessageTrimmerTranslator,
    Translator,
)
from personate.face.face import Face
from personate.memory.memory import Memory
from sqlitedict import SqliteDict
from personate.swarm.internal_message import InternalMessage
from personate.swarm.swarm import Swarm
from personate.utils.logger import logger

uvloop.install()
import asyncio
import os
import types
import random

# new_ranker.add_model("all-mpnet-base-v2")
import discord
import regex as re
from personate.prompts.frame import AgentFrame


class Agent:
    __instances__ = []
    def __init__(
        self,
        name: str,
        token: str,
        agent_dir: str,
        json_path: Optional[str] = None,
        no_webhooks: bool = False,
        adventures: bool = False,
        **kwargs: dict,
    ) -> None:
        self.asyn = Asynchronise()
        self.swarm = Swarm()
        self.adventures = adventures
        self.agent_dir = agent_dir
        if not os.path.exists(f"{self.agent_dir}"):
            os.mkdir(f"{self.agent_dir}")
        if not os.path.exists(f"{self.agent_dir}/knowledge"):
            os.mkdir(f"{self.agent_dir}/knowledge")
        self.ranker = Ranker()
        self.json_path: Optional[str] = json_path
        self.bot = discord.Bot(
            command_prefix=f"{name}!",
            heartbeat_timeout=13,
            intents=discord.Intents.all(),
        )
        self.no_webhooks = no_webhooks
        self.token = token
        self.name = name
        self.activator = Activator()
        self.activator.add_check(
            checker=lambda m: isinstance(m, discord.Message)
            and m.author.name != self.name
            and not m.content.startswith(f"{name}!"),
            mandatory=True,
        )
        self.pre_translator: Translator = EmptyTranslator()
        self.post_translator: Translator = EmptyTranslator()
        self.post_translator.add_translator(MessageTrimmerTranslator())
        self.post_translator.add_translator(DiscordResponseTranslator())
        self.document_collection = DocumentCollection(documents=[])
        self.prompt: AgentFrame = AgentFrame(name=self.name, swarm=self.swarm, parent=self)
        self.prompt.set_post_translator(self.post_translator)
        self.prompt.set_pre_translator(self.pre_translator)
        self.face: Optional[Face] = None
        self.document_queue: List[Coroutine] = []
        self.memory: Optional[Memory] = None
        self.modifier = None
        self.improv_generator = None
        self.register_all()
        self.__dict__.update(kwargs)
        self.__instances__.append(self)

    def add_pre_translator(self, translator: Translator) -> None:
        self.pre_translator.add_translator(translator)

    def add_filter(self, filter: Filter) -> None:
        if self.prompt:
            self.prompt.add_filter(filter)
        else:
            raise ValueError("You must use a prompt before you can add filters.")

    def add_post_translator(self, translator: Translator) -> None:
        self.post_translator.add_translator(translator)

    def add_abilities_from_file(self, filename: str) -> None:
        self.swarm.use_module(filename)

    def add_abilities_from_library(self, module: types.ModuleType):
        self.swarm.use_module(module.__name__, register_all=True)

    def add_abilities_from_inbuilt(self, *abilities, token: str):
        if not token:
            raise ValueError(
                "You must provide a RapidAPI token to use the inbuilt abilities."
            )
        pass

    # TODO: Add inbuilt abilities.

    def set_ranker(self, ranker: Ranker) -> None:
        self.ranker = ranker

    def add_activator(
        self,
        condition: Optional[str] = None,
        checker: Optional[Callable] = None,
        mandatory: bool = False,
        topic: Optional[str] = None,
        sides: Optional[int] = None,
        name: Optional[str] = None,
        **kwargs,
    ) -> None:
        self.activator.add_check(
            condition=condition,
            checker=checker,
            mandatory=mandatory,
            topic=topic,
            sides=sides,
            name=name,
            **kwargs,
        )
        logger.debug(f"{self.name} added activator: {condition}")

    def set_appearance(
        self,
        filename: Optional[str] = None,
        avatar_url: Optional[str] = None,
        username: Optional[str] = None,
        loading_message: Optional[str] = None,
    ) -> None:
        if filename:
            appearance_dict = json.load(open(filename))
            avatar_url = appearance_dict.get(
                "avatar_url",
                "https://i.gifer.com/embedded/download/ZlXo.gif",
            )
            username = appearance_dict.get("username", self.name)
            loading_message = appearance_dict.get("loading_message", "...loading...")
        if not avatar_url:
            avatar_url = "https://i.gifer.com/embedded/download/ZlXo.gif"
        if not username:
            username = self.name
        if not loading_message:
            loading_message = "https://i.gifer.com/embedded/download/ZlXo.gif"
        if avatar_url and username:
            self.face = Face(
                bot=self.bot,
                avatar_url=avatar_url,
                username=username,
                loading_message=loading_message,
            )

    def use_context_from(self, events: List[str]) -> None:
        self.prompt.set_examples(events)

    def use_annotations(self, annotations: dict[str, str]) -> None:
        self.prompt.set_pre_response_annotation(annotations.get("pre_response", ""))
        self.prompt.set_pre_conversation_annotation(
            annotations.get("pre_conversation", "")
        )
        self.prompt.set_introduction(annotations.get("introduction", ""))

    def use_db(self, database_filename: str) -> None:
        db = SqliteDict(database_filename, autocommit=True)
        self.memory = Memory(db)
        self.prompt.set_memory(self.memory)

    def add_knowledge(
        self,
        filename: str,
        pre_computed: bool = False,
        is_text: bool = False,
        is_url: bool = False,
        directory: Optional[str] = None,
    ) -> None:
        doc = None
        if pre_computed:
            doc = Document.deserialise(filename)
        if not directory:
            directory = self.agent_dir + "/knowledge"
        if is_url:
            doc = Document.from_url_or_file(
                source=filename,
                embedding_model=self.ranker.default_model,
                is_url=True,
                directory_to_dump=directory,
                split_into_sentences=False,
            )
        elif is_text:
            doc = Document.from_url_or_file(
                source=filename,
                embedding_model=self.ranker.default_model,
                is_file=True,
                directory_to_dump=directory,
            )
        if doc:
            self.document_queue.append(doc)

    def add_knowledge_directory(self, directory_name: str):
        files = os.listdir(directory_name)
        for f in files:
            if f.endswith(".json"):
                self.add_knowledge(f"{directory_name}/{f}", pre_computed=True)
            elif f.endswith(".txt"):
                self.add_knowledge(f"{directory_name}/{f}", is_text=True)
            else:
                logger.warning(
                    "Unrecognised file format. Try labelling it as either a .txt if it's plaintext or a .json if it's been precomputed. pdfs don't work."
                )

    async def assemble_documents(self):
        documents: tuple[Document] = await asyncio.gather(*self.document_queue)
        self.document_queue.clear()
        self.document_collection.extend_documents(list(documents))
        self.prompt.set_document_collection(self.document_collection)

    async def start(self):
        # tasks: List[Union[Coroutine, asyncio.Future]] = []
        await self.assemble_documents()
        await self.bot.start(self.token)

        # asyncio.gather(*tasks)

    def run(self):
        while True:
            try:
                asyncio.run(asyncio.wait_for(self.start(), timeout=400))
                self.bot.clear()
                self.register_listeners()
            except asyncio.TimeoutError:
                continue

    @classmethod
    async def start_all(cls, bot: Optional[discord.Bot] = None, token: Optional[str] = None):
        instances = cls.__instances__
        if bot and token:
            await asyncio.gather(*[instance.assemble_documents() for instance in instances])
            await bot.start(token)
            return
        else:
            await asyncio.gather(*[instance.start() for instance in instances])
    
    @classmethod
    def run_all(cls, bot: Optional[discord.Bot] = None, token: Optional[str] = None):
        instances = cls.__instances__
        while True:
            try:
                asyncio.run(asyncio.wait_for(cls.start_all(bot, token), timeout=400))
            except asyncio.TimeoutError:
                for agent in instances:
                    agent.bot.clear()
                    agent.register_listeners()
                continue

    async def add_document(self, doc: Document):
        self.document_collection.add_document(doc)

    def register_listeners(self):
        @self.bot.listen("on_message")
        @self.activator.check(inputs=True, keyword="message")
        async def receive_messages(message: discord.Message):
            asyncio.create_task(self.reply(message))

        @self.bot.listen("on_message_edit")
        @self.activator.check(inputs=True, keyword="after")
        async def receive_edited_messages(before: discord.Message, after: discord.Message):
            if after:
                asyncio.create_task(self.reply(after))

        @self.bot.listen("on_connect")
        async def register_cog():
            logger.debug(f"{self.name} is ready.")
            if not self.modifier:
                from personate.meta.inbuilt_commands import make_agent_modifier
                self.modifier = make_agent_modifier(self.bot, self, self.agent_dir)
                logger.debug(f"{self.name} registered inbuilt commands.")
            if not self.improv_generator and self.adventures:
                from personate.meta.improv_scenes import ImprovGenerator
                self.improv_generator = ImprovGenerator(self)
                logger.debug(f"{self.name} registered improv generator.")

        @self.bot.listen("on_reaction_add")
        async def receive_reacts(reaction: discord.Reaction, user: discord.User):
            # if the reaction emoji is a tick
            if not (
                reaction.emoji == "✅" and reaction.message.author.name == self.name
            ):
                return
            if not user.id == self.bot.owner_id:
                return
            agent_message_id = reaction.message.id
            if (
                not isinstance(reaction.message.embeds[0].footer.text, str)
                or not self.memory
            ):
                return
            agent_message: InternalMessage = self.memory.db[agent_message_id]
            user_message_id = agent_message.reply_to
            user_message: InternalMessage = self.memory.db[user_message_id]
            interaction = str(user_message) + "\n" + str(agent_message)
            logger.debug(
                f"{self.name} received positive feedback from this interaction: {interaction}"
            )
            self.prompt.examples.append(interaction)
            if not self.json_path:
                return
            with open(self.json_path, "r") as f:
                current_data = json.load(f)
            current_data["examples"].append(interaction)
            with open(self.json_path, "w") as f:
                json.dump(current_data, f, indent=3)

    async def reply(self, external_message_user: discord.Message):
        if (
            not isinstance(external_message_user.channel, discord.TextChannel)
            or not self.face or not self.memory
        ):
            return
        asyncio.create_task(add_replies_to_memory(self.memory, external_message_user, self.name))
        # Retrieves the reply-chain, if there is one.
        external_message_agent = await self.face.send_loading(
            external_message_user.channel
        )
        await self.prompt.translate_message_pair(
            external_message_agent=external_message_agent,
            external_message_user=external_message_user,
        )

    def register_all(self):
        self.register_listeners()

async def add_replies_to_memory(memory: Memory, message: discord.Message, name: str):
    last_20_messages = await message.channel.history(limit=10).flatten()
    for msg in last_20_messages:
        internal_msg = InternalMessage.from_discord_message(msg)
        try:
            reply_to = int(str(msg.embeds[0].footer.text))
            internal_msg.reply_to = reply_to
            logger.debug("I found a message by a Personate chatbot and added a reply to it")
        except:
            pass
        if not msg.id in memory.db.keys() and msg.author.name != name:
            memory.db[msg.id] = internal_msg
        else:
            logger.debug(f"I already have a message with id {internal_msg.id}")
