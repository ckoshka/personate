# Provides Translator objects, that handle specific objects and return 'translated' versions of them - e.g adding emojis, changing the language, correcting spelling, and so on.
from abc import ABC, abstractmethod, abstractproperty
from concurrent.futures import process
from typing import Optional, Union, Callable, List, Dict, Any, Tuple
from personate.utils.logger import logger
import types
import discord
from personate.swarm.internal_message import InternalMessage
from acrossword import Ranker
import random

class Translator:
    def __init__(self) -> None:
        self.translators: List[Union["Translator", Callable]] = []
        # self.permitted_types: List[type] = []

    def add_translator(self, translator: Union[Callable, "Translator"]) -> None:
        self.translators.append(translator)

    def retrieve_by_classname(
        self, classname: str
    ) -> Union[None, Callable, "Translator"]:
        for translator in self.translators:
            if isinstance(translator, Translator):
                if translator.__class__.__name__ == classname:
                    return translator
            else:
                if translator.__name__ == classname:
                    return translator
        return None

    async def translate(self, **kwargs) -> Any:
        for translator in self.translators:
            try:
                logger.debug(
                    "Name of function acting as translator: {}".format(
                        translator.__name__
                    )
                )
                # logger.debug("Message before translation: {}".format(**kwargs))
                if isinstance(translator, Translator):
                    await translator.translate(**kwargs)
                else:
                    await translator(**kwargs)
            except:
                logger.error(
                    "Error in translator: {}".format(translator.__name__), exc_info=True
                )
                continue
        return kwargs

    @classmethod
    def inputs(cls, **clskwargs) -> Callable:
        """Calls Translator.translate as a decorator"""
        instance = cls(**clskwargs)

        def wrapper(func: Callable) -> Callable:
            async def inner_wrapper(*args, **kwargs) -> Any:
                kwargs = await instance.translate(**kwargs)
                return await func(*args, **kwargs)

            return inner_wrapper

        return wrapper

    __name__ = "GenericBaseTranslator"


class DiscordResponseTranslator(Translator):
    __name__ = "DiscordResponseTranslator"

    def __init__(self):
        super().__init__()
        self.translators.append(self.add_response_embed)

    async def add_response_embed(
        self, agent_message: InternalMessage, user_message: discord.Message, **kwargs
    ):
        if agent_message and user_message:
            # logger.debug("Adding response embed to msg: {}".format(agent_message.__dict__))
            #avatar = None
            if user_message.author.avatar:
                avatar = user_message.author.avatar.url
            else:
                avatar = "https://www.google.com/nothing.png"
            message_id = user_message.id
            author_name = user_message.author.name
            contents = user_message.content
            embed = discord.Embed(description=contents)
            embed.set_author(name=author_name, icon_url=avatar)
            embed.set_footer(text=message_id)
            agent_message.embeds = [embed]
            # return "agent_message", agent_message
        else:
            raise ValueError("Agent message and user message must be provided.")


class MessageTrimmerTranslator(Translator):
    __name__ = "MessageTrimmerTranslator"

    def __init__(self):
        super().__init__()
        self.translators.append(self.trim_message)

    async def trim_message(self, agent_message: InternalMessage, **kwargs):
        agent_message.internal_content = (
            agent_message.internal_content[::-1]
            .split("<\n", 1)[-1][::-1]
            .replace(" ", "", 1)
        )
        agent_message.external_content = (
            agent_message.external_content[::-1]
            .split("<\n", 1)[-1][::-1]
            .replace(" ", "", 1)
        )
        agent_message.internal_content = agent_message.internal_content.strip()
        agent_message.external_content = agent_message.external_content.strip()
        # return "agent_message", agent_message


class CWTaggerTranslator(Translator):

    name = "CWTaggerTranslator"

    def __init__(
        self, topics: Optional[List[str]] = None, top_k: int = 1, **kwargs: dict
    ) -> None:
        super().__init__()
        self.translators.append(self.spoiler_text_and_add_cw_tag)
        self.possible_cw_tag_options: List[str] = []
        self.standard_boilerplate_prefix: str = (
            "This sentence is related to or involves "
        )
        self.neutral_options: List[str] = [
            "This sentence is unoffensive and contains no upsetting content",
            "This sentence is calm and factual",
            "This sentence is conversational and casual",
            "This sentence is not very interesting and talks about generic topics",
            "This sentence is about science, sports, art, or music",
        ]
        self.top_k: int = top_k
        if topics:
            for topic in topics:
                self.possible_cw_tag_options.append(
                    f"{self.standard_boilerplate_prefix} {topic}"
                )
        else:
            self.possible_cw_tag_options.extend(
                [
                    self.standard_boilerplate_prefix + opt
                    for opt in [
                        "sexually explicit content or erotica",
                        "violence",
                        "food",
                        "COVID-19 or disease",
                        "needles or injections",
                        "abuse or gaslighting",
                        "cruelty towards animals",
                        "mental illness or disorders",
                        "suicide or self-harm",
                        "racism, Nazism, or white supremacism",
                        "transphobia",
                        "queerphobia or anti-LGBTQ prejudice",
                        "anti-Semitism or anti-Jewish prejudice",
                    ]
                ]
            )
        self.possible_cw_tag_options.extend(self.neutral_options)
        self.__dict__.update(kwargs)

    def add_cw_topic(self, topic: str) -> None:
        self.possible_cw_tag_options.append(
            f"{self.standard_boilerplate_prefix} {topic}"
        )

    async def spoiler_text_and_add_cw_tag(
        self, agent_message: InternalMessage, **kwargs
    ) -> None:
        if not agent_message or (
            not agent_message.internal_content and agent_message.external_content
        ):
            return
        ranker = Ranker()
        top_labels: List[str] = await ranker.rank(
            texts=tuple(self.possible_cw_tag_options),
            query=agent_message.internal_content,
            top_k=self.top_k,
            model=ranker.default_model,
        )
        if top_labels[0] in self.neutral_options:
            return
        final_label = ", ".join(
            [
                topic.replace(self.standard_boilerplate_prefix, "")
                for topic in top_labels
            ]
        )
        agent_message.external_content = (
            f"CW {final_label} ||{agent_message.external_content}||"
        )


import random
import ujson as json


class EmojiTranslator(Translator):

    name = "EmojiTranslator"

    def __init__(
        self,
        emojis: Optional[Dict[str, list]] = None,
        file: Optional[str] = None,
        **kwargs: dict,
    ) -> None:
        super().__init__()
        self.translators.append(self.add_emoji_to_message)
        final_emojis = {}
        if emojis:
            emojis = {
                f"What is an example of a sentence expressing {k} in its tone or implication?": v
                for k, v in emojis.items()
            }
            for k in emojis:
                if isinstance(emojis[k], str):
                    emojis[k] = [emojis[k]]
            final_emojis.update(emojis)
        neutral = {
            # "This is a neutral sentence.": [""],
            # "This is a factual sentence": [""],
            # "This sentence doesn't express any particular emotion.": [""],
            # "This is a sentence that is not very interesting.": [""],
        }
        if file:
            with open(file, "r") as f:
                data = json.load(f)
            emojis = {k: v for k, v in data.items()}
            final_emojis.update(emojis)
        final_emojis.update(neutral)
        self.filename = file
        self.emojis = final_emojis
        self.__dict__.update(kwargs)

    def append_emoji(self, tags: str, emoji: Union[str, list]) -> None:
        if isinstance(emoji, str):
            emoji = [emoji]
        self.emojis[tags] = emoji
        if self.filename:
            with open(self.filename, "w") as f:
                json.dump(self.emojis, f, indent=4)

    async def add_emoji_to_message(self, agent_message: InternalMessage, **kwargs):
        ranker = Ranker()
        """Adds an emoji to the text provided based on its semantic similarity to the provided emojis and their labels, does not add an emoji if the result of rank is an empty list."""
        # emojis should look like {"happy, cheerful, good mood": ["<:happy:293844>", "<:some_other_emoji:293833>"]}, etc.
        logger.debug(
            f"I am adding an emoji to the message now: {agent_message.internal_content}"
        )
        top_labels: List[str] = await ranker.rank(
            texts=tuple(self.emojis.keys()),
            query=agent_message.internal_content,
            top_k=1,
            model=ranker.default_model,
        )
        logger.debug(f"The top labels are: {top_labels}")
        if top_labels:
            top_emojis: List[str] = self.emojis[top_labels[0]]
            top_emoji = random.choice(top_emojis)
            text = f"{agent_message.external_content} {top_emoji}"
            agent_message.external_content = text
        return


from personate.utils.apis import translate

# def translate(text: str, to_lang: str) -> str:
import pycld2 as cld2


import asyncio


class LanguageTranslator(Translator):
    def __init__(self, default_language_code: str = "en"):
        super().__init__()
        self.translators.append(self.translate_message)
        self.default_language_code = default_language_code

    async def translate_message(
        self,
        agent_message: InternalMessage,
        processed_user_message: InternalMessage,
        **kwargs: dict,
    ) -> None:
        if agent_message and processed_user_message:
            isReliable, textBytesFound, details = cld2.detect(
                processed_user_message.external_content
            )
            user_language = details[0][1]
            logger.debug(f"The user language is: {user_language}")
            if user_language != self.default_language_code and isReliable:
                try:
                    result = await translate(
                        agent_message.external_content, user_language
                    )
                    logger.debug(f"The result of the posttranslation is: {result}")
                    if result:
                        agent_message.external_content = result[0]
                except:
                    pass
        elif processed_user_message and not agent_message:
            isReliable, textBytesFound, details = cld2.detect(
                processed_user_message.internal_content
            )
            language = details[0][1]
            logger.debug(f"The language is: {language}")
            if language == self.default_language_code and isReliable:
                logger.debug(
                    f"The language is the same as the default language, so I am not translating."
                )
                return
            try:
                result = await translate(
                    processed_user_message.internal_content, self.default_language_code
                )
                logger.debug(f"The result of the pretranslation is: {result}")
                if result:
                    processed_user_message.internal_content = result[0]
            except:
                pass
        return


class EmptyTranslator(Translator):
    def __init__(self):
        super().__init__()
