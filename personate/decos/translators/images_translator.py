import asyncio
import random
from io import BytesIO
from typing import Optional

import aiohttp
import discord
import regex as re

# Example:
from bing_image_urls import bing_image_urls
from personate.decos.translators.translator import Translator
from discord import File
from personate.swarm.internal_message import InternalMessage
from personate.utils.logger import logger


class TextToImageTranslator(Translator):
    name = "TextToImageTranslator"

    def __init__(self, domain_url: Optional[str] = None):
        super().__init__()
        self.domain_url = domain_url
        self.translators.append(self.convert_to_image_attachment)

    async def convert_to_image_attachment(
        self, agent_message: Optional[InternalMessage] = None, **kwargs
    ):
        if not agent_message:
            return
        content = agent_message.external_content
        logger.debug("Content before translation: {}".format(content))
        # The content may look like [image: Schrodinger's cat diagram]
        # What this function does is captures the search query, uses the bing api to get a list of images, selects one at random, uses aiohttp to stream it into a BufferedIOBase, creates a discord.File object initialised using that BufferedIOBase, and sets agent_message.files to be a list of File objects (if there are multiple instances). The external content containing the [] is replaced with a caption.
        queries_matches = re.search(r"\[image: (.+?)\]", content)
        if not queries_matches:
            return
        queries = queries_matches.groups()
        logger.debug(f"Queries: {queries}")
        for query in queries:
            # Get current event loop
            loop = asyncio.get_event_loop()
            # Get a list of images from the bing api
            if self.domain_url:
                query = f"site:{self.domain_url} {query}"
            images = await loop.run_in_executor(None, bing_image_urls, query, 0, 15)
            logger.debug(f"Images: {images[:5]}")
            images = [im for im in images if im[-4] == "." and "gif" not in im]
            logger.debug(f"Images after filtering: {images[:5]}")
            # Select one at random
            image = random.choice(images)
            logger.debug(f"Chosen image: {image}")
            # Use aiohttp to stream the image into a BufferedIOBase
            was_successful = False
            while not was_successful:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image) as resp:
                            if resp.status == 200:
                                r = await resp.read()
                                # logger.debug(f"Response: {r}")
                                # Create a discord.File object initialised using that BufferedIOBase
                                r_bytes_io = BytesIO(r)
                                # logger.debug(f"BytesIO: {r_bytes_io}")
                                # Create a discord.File object using the BufferedIOBase
                                file = File(r_bytes_io, filename=image.split("/")[-1])
                                # If there are multiple instances of this, create a list of File objects
                                if isinstance(agent_message.files, list):
                                    agent_message.files.append(file)
                                else:
                                    agent_message.files = [file]
                                was_successful = True
                                break
                except Exception as e:
                    logger.error(f"Error: {e}")
                    image = random.choice(images)
                    continue
            query = query.replace(f"site:{self.domain_url} ", "")
            # Replace the external content containing the [] with ""
            content = re.sub(r"\[image: .+?\]", "", content)
            # [caption: {query}]?
            # Set the external content to be the new content
            agent_message.external_content = content
            logger.debug(f"Content after translation: {content}")


from personate.utils.apis import get_description_for_image


class ImageToTextTranslator(Translator):
    name = "ImageToTextTranslator"

    def __init__(self, domain_url: Optional[str] = None):
        super().__init__()
        self.domain_url = domain_url
        self.translators.append(self.convert_image_to_text)

    async def convert_image_to_text(
        self,
        original_user_message: discord.Message,
        processed_user_message: InternalMessage,
    ):
        images = [file for file in original_user_message.attachments]
        if not images:
            return
        descriptions = [await get_description_for_image(image.url) for image in images]
        # Add captions in the same format as the original message i.e [image: description]
        descriptions = "\n".join(
            [f"[image: {description}]" for description in descriptions]
        )
        processed_user_message.internal_content = descriptions
