import os
from typing import Optional
from urllib.parse import quote_plus

import ujson as json
from acrossword import Document
from personate.completions import default_generator_api
from personate.utils.logger import logger
from personate.utils.username_generator import username_generator

from personate.meta.standard.agents import Agent
import importlib.resources


class AgentFromJSON:
    available_presets = set(
        ["chatbot", "entity", "fictional_character", "historical_person", "assistant", "dm"]
    )

    available_preprocessors = ["translate", "images-to-text"]
    available_postprocessors = ["translate", "text-to-images"]

    @classmethod
    def from_json(cls, json_path: str) -> Agent:
        with open(json_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data, json_path=json_path)

    @classmethod
    def from_dict(cls, data: dict, json_path: Optional[str] = None) -> Agent:
        name = data.get("name", None)
        token = data.get("bot_token", None)
        reads = data.get("reads", False)
        debug = data.get("debug", False)
        preset = data.get("preset", None)
        no_webhooks: bool = data.get("no_webhooks", False)
        logger.debug(
            f"Initialising agent from json with {name}, {token}, {reads}, {debug}, {preset}"
        )

        none_errors = {
            "You need to specify a name for your agent. If you can't think of one, use a nondescript name then allow it to choose for itself.": name,
            "You need a Discord bot token to run your agent at the moment (but soon I'll add a console version) – this site will show you how: https://www.digitaltrends.com/gaming/how-to-make-a-discord-bot/": token,
            f"""Preset must be one of: {", ".join(cls.available_presets)}. Tip: use "preset: chatbot" if you're writing a unique character, and "entity" for anything that isn't listed – e.g abstract concepts, organisations, etc.""": preset
            in cls.available_presets,
        }
        collected_errors = [error for error, value in none_errors.items() if not value]
        if collected_errors:
            raise ValueError("\n".join(collected_errors))
        if not name or not token or not preset:
            raise ValueError("\n".join(collected_errors))

        home_dir = data.get("home_directory", "temp-" + name)
        if not os.path.exists(home_dir):
            os.mkdir(home_dir)
        logger.debug(f"Using home directory {home_dir}")

        agent = Agent(
            name=name,
            token=token,
            agent_dir=home_dir,
            json_path=json_path,
            no_webhooks=no_webhooks,
        )

        template_path = "personate.meta.templates.{}".format(preset)
        logger.debug(f"Using template {template_path}")
        if preset == "custom":
            template = __import__(template_path, fromlist=["template"]).template

            introduction = data.get("introduction", None)

            if not introduction:
                raise ValueError("You need to specify an introduction for your agent.")

            template["introduction"] = introduction
        else:
            template = __import__(template_path, fromlist=["template"]).template

            logger.debug(f"Using template {template}")
            authors = data.get("authors", None)

            if authors:
                template["introduction"] = template["introduction"].replace(
                    "{authors}", authors
                )
            else:
                template["introduction"] = template["introduction"].replace(
                    "{authors}", "experts"
                )
            logger.debug(f"Using authors {authors}")

            introduction = data.get("introduction", None)
            if not introduction and "{introduction}" in template["introduction"]:
                raise ValueError(
                    "You need to introduce your agent. Have a look at the example template."
                )
            if introduction:
                template["introduction"] = template["introduction"].replace(
                    "{introduction}", introduction
                )

            logger.debug(f"Using introduction {template['introduction']}")

        template = eval(str(template).replace("{chatbot_name}", name))

        agent.use_annotations(template)

        db_path = data.get("db_path", home_dir + "/db.sqlite")
        agent.use_db(db_path)
        logger.debug(f"Using db {db_path}")

        loading_message = data.get(
            "loading_message",
            "https://i.pinimg.com/originals/f1/79/90/f179907b01caacdc35af6a0f27bc6616.gif",
        )
        avatar = data.get("avatar", None)
        agent.set_appearance(
            avatar_url=avatar, loading_message=loading_message, username=name
        )
        logger.debug(f"Using avatar {avatar}")

        activators = data.get("activators", [])
        agent.add_activator(condition="on_ping", name=name)
        for act in activators:
            agent.add_activator(
                condition="on_topic",
                topic=act.get("listens_to"),
                ignore_topics=act.get("ignores", []),
            )
            logger.debug(f"Using activator {act}")

        examples = data.get("examples", [])
        if not examples and not preset == "dm":
            raise ValueError(
                "You need to specify some examples to use for your agent to show how it should react and behave."
            )
        examples_str = ""
        for example in examples:
            if isinstance(example, str):
                examples_str += example + "\n\n"
            elif isinstance(example, dict):
                if "user" in example.keys():
                    examples_str += f"<{username_generator()}>: {example['user']}\n"
                else:
                    custom_username = [
                        name for name in example.keys() if name != "agent"
                    ]
                    if custom_username:
                        examples_str += (
                            f"<{custom_username[0]}>: {example[custom_username[0]]}\n"
                        )
                if "source" in example.keys():
                    examples_str += f"(Source: \"{example['source']}\")\n"
                if "agent" in example.keys():
                    examples_str += f"<{name}>: {example['agent']}\n\n"
        agent.use_context_from(examples_str.split("\n\n"))

        # if reading list, first check if the urllib-encoded urls already exist in a knowledge subdirectory
        knowledge_directory = data.get("knowledge_directory", home_dir + "/knowledge")
        for file in os.listdir(knowledge_directory):
            agent.add_knowledge(
                filename=knowledge_directory + "/" + file,
                pre_computed=True,
            )
        reading_list = data.get("reading_list", [])
        for url in reading_list:
            if os.path.exists(knowledge_directory + "/" + quote_plus(url) + ".json"):
                continue
            else:
                if "http" in url or "www" in url:
                    agent.add_knowledge(url, is_url=True)
                    logger.debug(f"Using url knowledge {url}")
                else:
                    agent.add_knowledge(url, is_text=True)
                    logger.debug(f"Using text knowledge {url}")

        content_warning_topics = data.get("content_warning_topics", 2)
        if isinstance(content_warning_topics, list):
            from personate.decos.translators.translator import CWTaggerTranslator

            cw_tagger = CWTaggerTranslator(topics=content_warning_topics)
            agent.add_post_translator(cw_tagger)
            logger.debug(f"Using content warning topics {content_warning_topics}")

        preprocessor_list = set(data.get("preprocessors", [])) & set(
            cls.available_preprocessors
        )
        post_processor_list = set(data.get("postprocessors", [])) & set(
            cls.available_postprocessors
        )
        logger.debug(f"Using preprocessors {preprocessor_list}")
        logger.debug(f"Using postprocessors {post_processor_list}")

        if "translate" in preprocessor_list.union(post_processor_list):
            from personate.decos.translators.translator import LanguageTranslator

            translator = LanguageTranslator(default_language_code="en")
            if "translate" in preprocessor_list:
                agent.add_pre_translator(translator)
            if "translate" in post_processor_list:
                agent.add_post_translator(translator)
            logger.debug(f"Using language translator")

        if "text-to-images" in post_processor_list:
            from personate.decos.translators.images_translator import (
                TextToImageTranslator,
            )

            text_to_image_translator = TextToImageTranslator()
            agent.add_post_translator(text_to_image_translator)
            logger.debug(f"Using text-to-images translator")

        if "images-to-text" in preprocessor_list:
            from personate.decos.translators.images_translator import (
                ImageToTextTranslator,
            )

            image_to_text_translator = ImageToTextTranslator()
            agent.add_pre_translator(image_to_text_translator)
            logger.debug(f"Using images-to-text translator")

        emoji_file: str = data.get("emoji_file", None)
        emojis = data.get("emojis", dict())
        if emojis or emoji_file:
            from personate.decos.translators.translator import EmojiTranslator

            emoji_translator = EmojiTranslator(file=emoji_file, emojis=emojis)
            agent.add_post_translator(emoji_translator)
            logger.debug(f"Using emojis {emojis}")

        abilities_file = data.get("abilities_file", None)
        if abilities_file:
            agent.swarm.use_module(abilities_file, register_all=True)

        return agent
