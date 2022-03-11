import asyncio
import copy
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Iterable,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

import discord
from acrossword import Document, DocumentCollection
from personate.completions import default_generator_api
from personate.decos.filter import Filter, DefaultFilter
from personate.decos.translators.translator import EmptyTranslator, Translator
from personate.memory.memory import Memory
from personate.decos.translators.translator import (
    DiscordResponseTranslator,
    MessageTrimmerTranslator,
)
from personate.swarm.internal_message import InternalMessage
from personate.swarm.swarm import Swarm
from personate.utils.logger import logger

from personate.prompts.semantic_list import SemanticList

from asynchronise import Asynchronise


class Frame:
    def __init__(self, fields: List[Sequence[str]], generator_api: Callable):
        self.fields = fields
        self.field_values: dict[str, Union[str, List[str]]] = {}
        # A list of field-names and their default values if unspecified.
        # self.template = template
        # A string containing the template to be used for this frame.
        self.filters = []
        # A list of filters to be applied to the outputs.
        self.generator_api = generator_api

    async def as_string(self) -> str:
        logger.debug(self.fields)
        logger.debug(self.field_values)
        final_string = ""
        for field in self.fields:
            try:
                val = self.field_values[field[0]]
            except KeyError:
                val = field[1]
            if len(val) == 0:
                continue
            if isinstance(val, str):
                final_string += val
            elif isinstance(val, list):
                final_string += "\n".join(val)
            final_string += "\n"
        return final_string[:-1]

    def clone(self):
        new_frame = Frame(
            fields=copy.deepcopy(self.fields), generator_api=self.generator_api
        )
        new_frame.field_values = copy.deepcopy(self.field_values)
        new_frame.filters = self.filters
        return new_frame

    async def complete(self) -> str:
        prompt = await self.as_string()
        completion = None
        for i in range(5):
            completion = await self.generator_api(prompt=prompt)
            should_reject = await asyncio.gather(
                *[
                    f.validate(
                        response=completion,
                        final_prompt=prompt,
                    )
                    for f in self.filters
                ]
            )
            logger.debug(f"The Filters and their results were:")
            for f, b in zip(self.filters, should_reject):
                logger.debug(f.__class__.__name__, b)
            if not any(should_reject):
                break
        if completion:
            return completion
        else:
            raise Exception("No completion found.")


import random


class Turn:
    def __init__(self, id: int, **kwargs):
        self.id = id
        self.internal_message_agent: Optional[InternalMessage] = None
        self.external_message_agent: Optional[discord.Message] = None
        self.internal_message_user: Optional[InternalMessage] = None
        self.external_message_user: Optional[discord.Message] = None
        self.__dict__.update(kwargs)


class AgentFrame:
    """Wraps and manages a Frame object, with the responsibility of setting its values."""

    # asyncer = Asynchronise(name="agent frame asyncer")

    def __init__(self, name: str, swarm: Swarm, parent: Any, **kwargs):
        self.frame = Frame(
            fields=[
                ("introduction", ""),
                ("examples", ""),
                ("pre_conversation_annotation", ""),
                ("current_conversation", ""),
                ("pre_response_annotation", ""),
                ("reading_cue", ""),
                ("api_result", ""),
                ("speech_cue", f"<{name}>:"),
            ],
            generator_api=default_generator_api,
        )
        self.name = name
        self.parent = parent
        self.swarm = swarm
        self.examples = SemanticList()
        self.frame.filters = [DefaultFilter()]
        self.memory: Optional[Memory] = None
        self.turns: Dict[int, Turn] = {}
        self.document_collection: Optional[DocumentCollection] = None
        self.max_characters: int = 1000
        self.__dict__.update(kwargs)
        self.asyncer = Asynchronise(name="agent frame asyncer")
        self.register_listeners()
        # problem is copies and references. unclear as to how it should behave. clear? initialised each time? costly. would be convenient if memory retrieval, document search, and translation were all internal to the frame.
        # transformation + reordering.

    def add_filter(self, filter: Filter):
        self.frame.filters.append(filter)

    def set_memory(self, mem: Memory):
        self.memory = mem

    def set_pre_translator(self, translator: Translator):
        self.pre_translator = translator

    def set_post_translator(self, translator: Translator):
        self.post_translator = translator

    def set_document_collection(self, collection: DocumentCollection):
        self.document_collection = collection

    # def add_reading_cue(self, sources: str):
    # self.frame.field_values["reading_cue"] = f'(Sources: "{sources}")'

    # def add_api_result(self, result: str):
    # self.frame.field_values["api_result"] = f'(API result: "{result}")'

    def set_pre_response_annotation(self, annotation: str):
        self.frame.field_values["pre_response_annotation"] = annotation

    def set_pre_conversation_annotation(self, annotation: str):
        self.frame.field_values["pre_conversation_annotation"] = annotation

    # def set_current_conversation(self, conversation: List[Any]):
    # self.frame.field_values["current_conversation"] = "\n".join(
    # [str(c) for c in conversation]
    # )

    def set_examples(self, examples: List[Any]):
        self.examples = SemanticList([str(c) for c in examples if len(str(c)) > 0])

    def set_introduction(self, introduction: str):
        self.frame.field_values["introduction"] = introduction

    async def retrieve_reply_chain(
        self, internal_message_user: InternalMessage
    ) -> List[InternalMessage]:
        if not self.memory:
            raise Exception("No memory object set.")
        message_chain = await self.memory.retrieve_reply_chain(
            message=internal_message_user, max_characters=self.max_characters
        )
        return message_chain

    async def _generate_reply(
        self,
        external_message_user: discord.Message,
        external_message_agent: discord.Message,
    ) -> InternalMessage:
        """Generates a reply to a user message."""
        internal_message_user = InternalMessage.from_discord_message(
            external_message_user
        )
        internal_message_agent = InternalMessage.from_discord_message(
            external_message_agent
        )
        turn = Turn(
            id=external_message_user.id,
            external_message_user=external_message_user,
            external_message_agent=external_message_agent,
            internal_message_user=internal_message_user,
            internal_message_agent=internal_message_agent,
        )
        self.turns[turn.id] = turn

        if not self.memory:
            raise Exception("No memory set.")
        if not (
            turn.internal_message_user
            and turn.internal_message_agent
            and turn.external_message_user
            and turn.external_message_agent
        ):
            raise Exception("No user message set.")
        # pronouns = self.memory.db.get("pronouns", {}).get(turn.internal_message_user.author_id, None)
        # logger.debug(f"Pronouns: {pronouns}")
        # logger.debug(f'Pronouns db: {self.memory.db.get("pronouns", None)}')
        # if pronouns:
        # turn.internal_message_user.name += f" ({pronouns})"
        # logger.debug(f"Name of user: {turn.internal_message_user.name}")
        # if not external_message_user.id in self.memory.db.keys():
        await self.pre_translator.translate(
            processed_user_message=turn.internal_message_user,
            original_user_message=turn.external_message_user,
        )
        if not external_message_user.id in self.memory.db.keys():
            self.memory.insert_message(external_message_user.id, turn.internal_message_user)
        # else:
        # turn.internal_message_user = self.memory.db[external_message_user.id]

        frame = self.frame.clone()

        frame.field_values["current_conversation"] = "\n".join(
            [
                str(c)
                for c in await self.memory.retrieve_reply_chain(
                    message=turn.internal_message_user,
                    max_characters=self.max_characters,
                )
            ]
        )

        frame.field_values["examples"] = await self.examples.reordered(
            query=frame.field_values["current_conversation"][-120:]
        )

        api_result_task = asyncio.create_task(
            self.swarm.solve(turn.internal_message_user.internal_content)
        )

        if self.document_collection and len(self.document_collection.documents) > 0:
            top_results = [
                r.replace("\n", " ")
                for r in await self.document_collection.search(
                    frame.field_values["current_conversation"][-120:], top=3
                )
            ]
            as_str = "\n".join(top_results)
            if as_str:
                frame.field_values["reading_cue"] = f'(Sources: "{as_str}")'

        api_result = await api_result_task
        if api_result:
            frame.field_values["api_result"] = f'(API result: "{api_result}")'

        completion = await frame.complete()
        turn.internal_message_agent.reply_to = turn.external_message_user.id
        turn.internal_message_agent.internal_content = completion
        turn.internal_message_agent.external_content = completion
        turn.internal_message_agent.name = self.name
        await self.post_translator.translate(
            completion=completion,
            agent_message=turn.internal_message_agent,
            user_message=turn.external_message_user,
            processed_user_message=turn.internal_message_user,
        )
        self.memory.insert_message(
            external_message_agent.id, turn.internal_message_agent
        )
        return turn.internal_message_agent

    async def translate_message_pair(
        self,
        external_message_user: discord.Message,
        external_message_agent: discord.Message,
    ):
        @self.asyncer.send
        async def translate_message_pair(
            external_message_user: discord.Message,
            external_message_agent: discord.Message,
        ):
            yield external_message_user, "external_message_user"
            yield external_message_agent, "external_message_agent"
            if not self.memory:
                return
            if not external_message_user.id in self.memory.db.keys():
                internal_message_user = InternalMessage.from_discord_message(
                    external_message_user
                )
                try:
                    reply_to = int(str(external_message_user.embeds[0].footer.text))
                    internal_message_user.reply_to = reply_to
                    logger.debug("I found a message by a Personate chatbot and added a reply to it")
                except:
                    pass
                logger.debug(f"User message was not in db: {internal_message_user}")
            else:
                internal_message_user = self.memory.db[external_message_user.id]
                logger.debug(f"User message was in db: {internal_message_user}")
            internal_message_agent = InternalMessage.from_discord_message(
                external_message_agent
            )
            await self.pre_translator.translate(
                processed_user_message=internal_message_user,
                original_user_message=external_message_user,
            )
            self.memory.insert_message(external_message_user.id, internal_message_user)
            yield internal_message_user, "internal_message_user"
            yield internal_message_agent, "internal_message_agent"

        async for e in translate_message_pair(
            external_message_user, external_message_agent
        ):
            pass

    def register_listeners(self):
        @self.asyncer.send
        @self.asyncer.collect(
            {"internal_message_user": (InternalMessage, "internal_message_user", None)}
        )
        async def get_current_conversation(internal_message_user: InternalMessage):
            if not self.memory:
                yield None, "current_conversation"
                return
            conversation = await self.memory.retrieve_reply_chain(
                message=internal_message_user, max_characters=self.max_characters
            )
            yield "\n".join([str(c) for c in conversation]), "current_conversation"

        @self.asyncer.send
        @self.asyncer.collect(
            {"internal_message_user": (InternalMessage, "internal_message_user", None)}
        )
        async def get_api_result(internal_message_user: InternalMessage):
            api_result = await self.swarm.solve(internal_message_user.internal_content)
            yield api_result, "api_result"

        @self.asyncer.send
        @self.asyncer.collect(
            {"current_conversation": (str, "current_conversation", None)}
        )
        async def get_document_results(current_conversation: str):
            if not self.document_collection:
                yield None, "reading_cue"
                return
            top_results = [
                r.replace("\n", " ")
                for r in await self.document_collection.search(
                    current_conversation[-120:], top=3
                )
            ]
            yield "\n".join(top_results), "reading_cue"

        @self.asyncer.send
        @self.asyncer.collect(
            {
                "current_conversation": (str, "current_conversation", None),
            }
        )
        async def get_examples(current_conversation: str):
            yield await self.examples.reordered(
                query=current_conversation[-120:]
            ), "examples"

        @self.asyncer.send
        @self.asyncer.collect(
            {
                "current_conversation": (str, "current_conversation", None),
                "api_result": (None, "api_result", None),
                "reading_cue": (None, "reading_cue", None),
                "examples": (None, "examples", None),
            }
        )
        async def get_frame(
            current_conversation: str, api_result: str, reading_cue: str, examples: str
        ):
            frame = self.frame.clone()
            frame.field_values["current_conversation"] = current_conversation
            if api_result:
                frame.field_values["api_result"] = f'(API result: "{api_result}")'
            if reading_cue:
                frame.field_values[
                    "reading_cue"
                ] = f'(Source: "{reading_cue}")'
            if examples:
                frame.field_values["examples"] = examples
            yield frame, "frame"

        @self.asyncer.send
        @self.asyncer.collect({"frame": (Frame, "frame", None)})
        async def get_completion(frame: Frame):
            completion = await frame.complete()
            yield completion, "completion"

        @self.asyncer.send
        @self.asyncer.collect(
            {
                "internal_message_agent": (
                    InternalMessage,
                    "internal_message_agent",
                    None,
                ),
                "completion": (str, "completion", None),
                "external_message_user": (
                    discord.Message,
                    "external_message_user",
                    None,
                ),
            }
        )
        async def post_translation(
            internal_message_agent: InternalMessage,
            completion: str,
            external_message_user: discord.Message,
        ):
            internal_message_agent.reply_to = external_message_user.id
            internal_message_agent.external_content = completion
            internal_message_agent.internal_content = completion
            internal_message_agent.name = self.name
            await self.post_translator.translate(
                completion=completion,
                agent_message=internal_message_agent,
                user_message=external_message_user,
                processed_user_message=internal_message_agent,
            )
            yield internal_message_agent, "internal_message_agent_complete"
            if not self.memory:
                return
            self.memory.insert_message(
                internal_message_agent.id, internal_message_agent
            )

        @self.asyncer.collect(
            {
                "internal_message_agent": (
                    InternalMessage,
                    "internal_message_agent_complete",
                    None,
                ),
                "external_message_agent": (
                    discord.Message,
                    "external_message_agent",
                    None,
                ),
                "external_message_user": (
                    discord.Message,
                    "external_message_user",
                    None,
                ),
            }
        )
        async def post_message(
            internal_message_agent: InternalMessage,
            external_message_agent: discord.Message,
            external_message_user: discord.Message,
        ):
            if self.parent.no_webhooks:
                await self.parent.face.reply_and_delete(
                    internal_message_agent,
                    external_message_agent,
                    external_message_user,
                )
                return
            if isinstance(external_message_agent, discord.WebhookMessage):
                await self.parent.face.update(
                    internal_message_agent, external_message_agent
                )
