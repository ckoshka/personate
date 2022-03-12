from typing import Optional
from pyai21.interpret import interpret

# Uncomment out emojify and add the name of the agent you want emojis for. You probably don't want a Dalek to be typing like a Japanese teenager for example.

#@emojify("examples_config/emojis.json", names=["Cinnamon"])
@interpret(maximum_similarity=70, max=200, stops=["<", "\n(", "\n"], frequency_penalty=47, temp=0.88)
async def generate_dialogue(
    name: str,
    description: str,
    conversation: str,
    is_ai: bool = False,
    examples: Optional[list] = None,
    facts: Optional[str] = None,
    response_type: str = "interesting and conversationally-engaging",
    annotation: str = "",
) -> str:
    if is_ai:
        ai_sentence = "Note that despite being specified as an AI, we chose to act as a human-level AI and to speak naturally, with artistic flair and personality. "
    else:
        ai_sentence = ""
    if examples:
        examples_sentence = (
            "\n\nHere are some example dialogues that we sketched out that really capture the voice and tonality of the character:\n"
            + "\n".join(examples)
            + "\n\n"
        )
    else:
        examples_sentence = ""
    if facts:
        facts_sentence = f"\nWe were also given these facts, which we were told to be absolutely consistent with:\n{facts}"
    else:
        facts_sentence = ""
    if annotation:
        annotation = f"(Quick note, and we promise there won't be any more commentary after this: {annotation})"
    return f"""
Something that our team enjoyed recently was being given randomly-generated character descriptions, then writing rich, detailed, convincing dialogues. The plot-twist: those dialogues occur in a modern Discord chatroom. So, we present to you, the character description:

{description}{facts_sentence}

Yup, that's it. {ai_sentence}{examples_sentence}And now, the full 2000-word dialog where we gave the character a unique, distinct voice and typing style. Users submitted questions to us and had long conversations, and we gave responses that were {response_type} (luckily we had expert researchers and specialists on the team – sometimes it took us up to three hours to craft the perfect answer):

{conversation}
<{name}>"""
