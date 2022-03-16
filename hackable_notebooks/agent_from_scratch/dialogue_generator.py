from typing import Optional
from pyai21.interpret import interpret

# Uncomment out emojify and add the name of the agent you want emojis for. You probably don't want a Dalek to be typing like a Japanese teenager for example.

#@emojify("examples_config/emojis.json", names=["Cinnamon"])
@interpret(maximum_similarity=70, max=400, stops=["<", "\n(", "\n"], presence_penalty=0.23, temp=0.865,)
async def generate_dialogue(
    name: str,
    description: str,
    conversation: str,
    is_ai: bool = False,
    examples: Optional[list] = None,
    facts: Optional[str] = None,
    response_type: str = "concise, interesting and conversationally-engaging",
    annotation: str = "",
    **kwargs
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
    if not response_type:
        response_type = "concise, interesting and conversationally-engaging"
    if facts:
        facts_sentence = f"\nWe were also given these facts, which we were told to be absolutely consistent with:\n{facts}"
    else:
        facts_sentence = ""
    if annotation:
        annotation = f"(Quick note, and we promise there won't be any more commentary after this: {annotation})\n"
    else:
        annotation = ""
    return f"""
Something that our team enjoyed recently was being given randomly-generated character descriptions, then writing rich, detailed, convincing dialogues. The plot-twist: those dialogues occur in a modern Discord chatroom. So, we present to you, the character description:

{description}{facts_sentence}

Yup, that's it. {ai_sentence}{examples_sentence}And now, the full 2000-word dialog where we give the character its unique, distinct voice and typing style. Users submitted questions to us and had long conversations, and we gave responses that were {response_type} (luckily we had expert researchers and specialists on the team – sometimes it took us up to three hours to craft the perfect answer):

{conversation}
{annotation}<{name}>"""

@interpret(maximum_similarity=65, max=400, stops=["<", "\n(", "\n"], presence_penalty=0.23, temp=0.865,)
async def generate_dialogue_chatbot(
    name: str,
    description: str,
    conversation: str,
    examples: Optional[list] = None,
    facts: Optional[str] = None,
    response_type: str = "concise, interesting and conversationally-engaging",
    annotation: str = "",
    **kwargs
) -> str:
    if annotation:
        annotation = f"(Quick note, and we promise there won't be any more commentary after this: {annotation})\n"
    return f"""({description}. Some additional trivia facts about {name} are: {facts}
    
    {name} doesn't exist yet, because AI isn't advanced enough, so here are all the ideal conversations our team of award-winning creative writers and avid researchers wrote while pretending to be {name} on Discord.)
    
    (From Discord on Jan 11, 2022, 4 messages):
    {examples}

    (Here, when completely different people asked the same questions as last time, we gave responses consistent with the previous conversation, but rewritten so they didn't sound repetitive or canned. We want {name} to sound like a real person, not a chatbot, so we will never write things in the exact same way twice. What we aimed for most, however, was to make our responses {response_type})
    
    (From Discord on 23 Feb 2022, 200 messages):
    {conversation}
    {annotation}<{name}>"""