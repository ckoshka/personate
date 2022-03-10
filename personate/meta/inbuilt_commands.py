# This allows you to make modifications to your bot from the convenience of Discord.

# TODO: Add items manually to contextual memory? By approving and de-approving responses, or selecting the best ones out of a group of 3? Via tick emoji.
# able to bring together existing discord bot and the chatbot, e.g cogs, slash commands, etc.
import asyncio
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)

import discord
import ujson as json
from acrossword import Document
from acrossword.documents.documents import DocumentCollection
from discord import commands
from personate.decos.translators.translator import EmojiTranslator
from personate.meta.standard.agents import Agent
from personate.utils.logger import logger
from personate.utils.username_generator import username_generator


def to_list(item: str) -> List[str]:
    return item.split("\n")


from personate.utils.commands import CommandRegister


def make_agent_modifier(bot: discord.Bot, agent: Agent, agent_dir: str):
    cr = CommandRegister(bot=bot, name=agent.name)

    class AgentModifier:
        def __init__(self, bot: discord.Bot, agent: Agent, agent_dir: str) -> None:
            self.bot: discord.Bot = bot
            self.agent: Agent = agent
            self.agent_dir: str = agent_dir

        @cr.register(owner=True)
        async def read(self, ctx: discord.Message, urls: str):
            await ctx.channel.send("reading!")
            url_list = to_list(urls)
            documents = [
                await Document.from_url_or_file(
                    source=url,
                    embedding_model=self.agent.ranker.default_model,
                    is_url=True,
                    directory_to_dump=self.agent_dir + "/knowledge",
                )
                for url in url_list
            ]
            # logger.info(f"Reading {len(docs)} documents.")
            await ctx.channel.send(f"Adding {len(documents)} documents.")
            # documents = await asyncio.gather(*[d for d in docs])
            logger.info(f"Finished processing {len(documents)} documents.")
            for doc in documents:
                await self.agent.add_document(doc)
            await ctx.channel.send(
                f"I have added the following documents to {self.agent.name}'s database: \n{urls}"
            )

        @cr.register(owner=True)
        async def remember(self, ctx: discord.Message, fact: str):
            await ctx.channel.send("Remembering!")
            collection: DocumentCollection = self.agent.document_collection
            try:
                doc = collection.retrieve("facts")
                await doc.add_chunk(fact)
                await doc.serialise()
            except IndexError:
                await ctx.channel.send("No facts found. Creating new facts document.")
                doc = await Document.from_sentences(
                    source=[fact],
                    source_name="facts",
                    directory_to_dump=self.agent_dir + "/knowledge",
                    embedding_model=self.agent.ranker.default_model,
                )
                collection.add_document(doc)
                await doc.serialise()
            await ctx.channel.send("Remembering complete.")

        @cr.register(owner=True)
        async def changetemplate(self, ctx: discord.Message):
            if not self.agent.prompt:
                return
            logger.info(f"Changing intro for {self.agent.name}.")
            old_intro = self.agent.prompt.frame.field_values["introduction"]
            await ctx.channel.send(f"Your current intro is:")
            await ctx.channel.send(f"{old_intro}")
            await ctx.channel.send(f"Please reply with the new intro.")
            new_intro = await self.bot.wait_for(
                "message", check=lambda m: m.author == ctx.author
            )
            self.agent.prompt.frame.field_values["introduction"] = new_intro.content
            await ctx.channel.send(f"Your new intro is:")
            await ctx.channel.send(f"{new_intro.content}")
            if self.agent.json_path:
                with open(self.agent.json_path, "r") as f:
                    data = json.load(f)
                data["introduction"] = new_intro.content
                with open(self.agent.json_path, "w") as f:
                    json.dump(data, f)

        @cr.register(owner=True)
        async def addexample(self, ctx: discord.Message, example: str):
            if "->" in example:
                username = username_generator()
                agentname = self.agent.name
                if example.count("->") == 1:
                    user, agent = example.split(" -> ")
                    example = f"<{username}>: {user}\n<{agentname}>: {agent}"
                else:
                    user, source, agent = example.split(" -> ")
                    example = f'<{username}>: {user}\n(Source: "{source}")\n<{agentname}>: {agent}'
            logger.info(f"Adding example to {self.agent.name}:\n{example}")
            if not self.agent.prompt:
                return
            # example = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author)
            await ctx.channel.send(f"Adding example: {example}")
            self.agent.prompt.examples.append(example)
            await ctx.channel.send(f"Example added.")
            if self.agent.json_path:
                with open(self.agent.json_path, "r") as f:
                    data = json.load(f)
                data["examples"] = self.agent.prompt.examples
                with open(self.agent.json_path, "w") as f:
                    json.dump(data, f)

        @cr.register(owner=True)
        async def teachemoji(self, ctx: discord.Message, emoji: str, description: str):
            await ctx.channel.send(f"Setting emoji to {emoji}")
            retrieved_translator = self.agent.post_translator.retrieve_by_classname(
                "EmojiTranslator"
            )
            if isinstance(retrieved_translator, EmojiTranslator):
                retrieved_translator.append_emoji(tags=description, emoji=emoji)
            await ctx.channel.send(
                f"I have added the following emoji to {self.agent.name}'s translator: \n{emoji}"
            )
            logger.info(f"Emoji added to {self.agent.name}'s translator.")

        @cr.register()
        async def addpronouns(self, ctx: discord.Message, pronoun: str):
            await ctx.channel.send(f"Registering your pronouns as {pronoun}")
            if not self.agent.prompt.memory or not ctx.author:
                return
            db = self.agent.prompt.memory.db
            if not db:
                return
            if "pronouns" not in db.keys():
                db.set("pronouns", {ctx.author.id: pronoun})
            current_pronouns = db.get("pronouns")
            current_pronouns[ctx.author.id] = pronoun
            db.set("pronouns", current_pronouns)
            db.commit()

        @cr.register(owner=True)
        async def addgoal(self, ctx: discord.Message, goal: str):
            last_line = self.agent.prompt.frame.field_values[
                "pre_conversation_annotation"
            ]
            if not isinstance(last_line, str):
                return
            last_line = last_line.split("\n\n")[-1]
            if "Note: in this conversation" in last_line:
                self.agent.prompt.frame.field_values[
                    "pre_conversation_annotation"
                ] = last_line.replace(
                    last_line,
                    f"(Note: in this conversation, we skillfully direct the conversation to attempt to {goal})",
                )
            else:
                self.agent.prompt.frame.field_values[
                    "pre_conversation_annotation"
                ] += f"\n(Note: in this conversation, we skillfully direct the conversation to attempt to {goal})"
            await ctx.channel.send(f"Changed goal to: {goal}")

            "  MISSION: "

        @cr.register(owner=True)
        async def addmission(self, ctx: discord.Message, goal: str):
            last_line = self.agent.prompt.frame.field_values[
                "pre_conversation_annotation"
            ]
            if not isinstance(last_line, str):
                return
            last_line = last_line.split("\n\n")[-1]
            if "MISSION:" in last_line:
                self.agent.prompt.frame.field_values[
                    "pre_conversation_annotation"
                ] = last_line.replace(
                    last_line,
                    f"(MISSION: {goal})",
                )
            else:
                self.agent.prompt.frame.field_values[
                    "pre_conversation_annotation"
                ] += f"\n(MISSION: {goal})"
            await ctx.channel.send(f"Changed mission to: {goal}")

    am = AgentModifier(bot=bot, agent=agent, agent_dir=agent_dir)
    cr.tied_to = am
    return am
