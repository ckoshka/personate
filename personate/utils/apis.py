import json
from pyrapidapi import APIManager
from typing import Tuple, Coroutine
from dotenv import load_dotenv

load_dotenv()
import os

key = os.getenv("RAPID_API_KEY")
if not key:
    raise Exception("RAPID_API_KEY not set in .env")

apis = APIManager(key)


@apis.json_decode("text")
@apis.post(
    "https://microsoft-translator-text.p.rapidapi.com/translate?",
    "microsoft-translator-text.p.rapidapi.com",
)
def translate(text: str, to_lang: str) -> Coroutine[Tuple[str, dict], None, None]:
    """This function translates text from one language to another.
    :param text: The text to translate.
    :param to_lang: The language to translate to.
    :return: The translated text.
    e.g "I would like coffee" in Russian -> "Я хочу кофе"
    """
    return json.dumps([{"text": text}]), {
        "to": to_lang,
        "api-version": "3.0",
        "includeAlignment": "false",
        "profanityAction": "NoAction",
        "textType": "plain",
    }  # type: ignore


@apis.get("wordsapiv1.p.rapidapi.com")
def info_for_word(info_type: str, word: str) -> str:
    return f"https://wordsapiv1.p.rapidapi.com/words/{word}/{info_type}"


# from api_decorators import json_decode, post, get as get_json
# import ujson as json


@apis.json_decode("text")
@apis.post(
    "https://microsoft-computer-vision3.p.rapidapi.com/describe?",
    "microsoft-computer-vision3.p.rapidapi.com",
)
def get_description_for_image(url: str) -> Coroutine[Tuple[str, dict], None, None]:
    """This function returns the description of an image.
    :param url: The url of the image to get the description of.
    :return: The description of the image as a list."""
    return json.dumps({"url": url}), {
        "language": "en",
        "maxCandidates": "1",
    }  # type: ignore
