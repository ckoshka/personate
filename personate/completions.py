from pyai21 import get


async def default_generator_api(prompt: str) -> str:
    """This function returns the text of a prompt according to settings specialised for usage with Agents.
    :param prompt: The prompt to get the text of.
    :return: The text of the prompt."""
    res = await get(
        prompt=prompt,
        stops=[">:", "From Discord", "From IRC", "\n(", "(", "> :", ">", "(Sources"],
        max=250,
        presence_penalty=0.23,
        temp=0.865,
    )
    if isinstance(res, list):
        return res[0]
    else:
        return res
