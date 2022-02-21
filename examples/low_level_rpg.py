from completions.prompt import Prompt
from documents.documents import Document, Searchable
from completions.completions import get as get_completion
from textwrap import dedent

class HistoryPrompt(Prompt):

    def __init__(self, username: str, world: Searchable) -> None:

        super().__init__()
        self.username = username

        self.template = f"""I had a lot of fun with my friends recently, as the DM for an online RPG called "The Butler Didn't It", a time travelling murder mystery that obeys Novikov's self-consistency principle. Here are the full transcripts below, where I played with {username} (with reference to the manual, of course):

        --

        {lines}
        """

        # Usually, the prompt wouldn't be initialised in such a static way.
        # For instance, you could have a Swarm generate a scenario based on
        # the user's provided genre, then use that as the template.

        self.lines = [
            "<DM> You wake up, nauseated, head resting against a display case, and groan loudly. You don't remember what happened last night, but it involved a museum curator and a large supply of absinthe. Immediately, you see something written on your palm."
            f"<{username}> read it \n(The manual: \"At the beginning of the story, the protagonist is in a museum. On their palm is written the message 'The Butler didn't it'\") \n <DM> You read the hastily-jotted scrawl, and find that it says: \"The Butler didn't it.\" It's in your handwriting."
        ]

        # This does something very important: it establishes a consistent 
        # format (IRC chatlogs) that the AI is likely to recognise.

        # The typical pattern in interactive prompts looks like:
        # 1. Interaction: the user does or says something, or an event occurs.
        # (In the background, it gets "translated" – for instance, spelling.)
        # 2. Cue-cards: these act as control-codes or suggestions for the AI.
        # They can either directly suggest what to do, or provide information
        # that allows it to decide.
        # 3. Response: the AI responds to the user's input.
        # (This response might be sent to other Prompts to be cleaned up.)

        self.world = world

    async def add_user_action(self, user_action: str) -> None:
        action = f"<{self.username}> {user_action}"
        self.lines.append(action)

    async def add_world_information(self) -> None:
        last_two_turns = '\n'.join(self.lines[-2:])
        top_relevant_facts = await self.world.search(
            query=last_two_turns, 
            top=3
        )

        world_info = f"(The manual: {'. '.join(top_relevant_facts)})"
        self.lines[-1] += "\n" + world_info

    async def get_response_for_action(self, user_action: str) -> str:
        await self.add_user_action(user_action)
        await self.add_world_information()
        final_str = self.finalise()
        dm_response = await get_completion(
            prompt=final_str, 
            max=200, 
            stops=[f'<self.username>', '\n']
        )
        self.lines[-1] += f"<DM> {dm_response}"
        return dm_response

    def finalise(self) -> str:
        prompt = self.template.format(
            username=self.username,
            lines='\n'.join(self.lines[-7:]) 
        ) + "\n<DM>"
        return prompt

        # We have to restrict ourselves to the last 7 turns
        # because the AI can only remember 2000 words at a time.
        # What we're doing with the world-doc is niftily getting
        # around that.

        # Note that in the Agent example, the Agent is dynamically
        # reordering its own conversation history. You could 
        # pretty much do the same thing here.

world = Document.from_url_or_file(
    source="butler_didnt_it.txt",
    is_file=True
)

# This is actually a very low-level example of what it's possible
# to do with the existing API. The finalised API might look something
# like this:

"""
from personate import World
from discord import Bot
bot = Bot()
world = World(
    factsheet="factsheet.json",
    bot_token="token",
    bot=bot
)
world.run()
"""

# In a more developed example, we would add some temporality to
# this world and update the world-facts as the story progresses,
# but for now, we'll just use the static world-facts.

import pickle

class YourDatabaseHere:
    def __init__(self):
        self.users: Dict[str, Prompt] = dict()
    async def get_prompt(self, username: str) -> "Prompt":
        return self.users.get(username, HistoryPrompt(username, world))
    def save_progress(self) -> None:
        with open('your_database_here.pickle', 'wb') as f:
            pickle.dump(self, f)

import asyncio
import os

async def main():

    if os.path.exists('your_database_here.pickle'):
        with open('your_database_here.pickle', 'rb') as f:
            db = pickle.load(f)
    else:
        db = YourDatabaseHere()

    username = input("What's your name? ")
    prompt = await db.get_prompt(username)

    print("The story so far...")
    for line in prompt.lines:
        print(line)
    print("Now the fun begins...")

    while True:
        user_action = input(f"{username}> ")
        if user_action == "quit":
            break
        dm_response = await prompt.get_response_for_action(user_action)
        print("<DM> " + dm_response)
    db.save_progress()





