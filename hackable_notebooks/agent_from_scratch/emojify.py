import json
from acrossword import Ranker
import random
from typing import Optional

def emojify(emoji_file: str, names: Optional[list[str]] = None):
    with open(emoji_file, "r") as f:
        emojis = json.load(f)
    ranker = Ranker()
    def outer_wrapper(func):
        async def wrapper(*args, **kwargs):
            if not "name" in kwargs:
                name = args[0]
            else:
                name = kwargs["name"]
            result = await func(*args, **kwargs)
            if names and name in names:
                top_emoji = await ranker.rank(texts=tuple(emojis.keys()), query=result, top_k=1, model=ranker.default_model)
                return f"{result} {random.choice(emojis[top_emoji[0]])}"
            else:
                return result
        return wrapper
    return outer_wrapper
    # This adds an emoji to the string result of an async function. You can use it for whatever.