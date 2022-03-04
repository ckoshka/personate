This is useful if you want to dive into the library and do some customisation. Otherwise, probably just stick with the json file config.

# Agent

Agent is a stupidly complex object that *will* cry if you initialise it in the wrong order and then try to run it, so pay close attention. We're going to make an Agent called Ziggy that acts as a personification of the Zig programming language, assuming you did all the setup mentioned in the readme.

### How it works - a high-level overview

* Memory stores past messages
* Face posts replies
* Activator filters new messages to see whether they're directed at the Agent
* DocumentCollection stores relevant information, like the number of moons in the solar system or whatever
* Swarm calls APIs as appropriate to augment the Agent with additional information, like the weather, the output of a command, etc.
* Frame is doing most of the heavy-lifting here while Agent is just a convenient wrapper for initialising them together.

## Anatomy of a Frame

Frames look like this, when converted to strings:

```
{INTRODUCTION - the bit introducing the Agent, what its personality is like, who supposedly crafted it, etc.}
{EXAMPLE_CONVERSATIONS} - the 5-6 most relevant past examples of how the Agent should ideally behave
{DIVIDER} - optional, something that just says "hey, this is a whole different conversation, so ignore the previous people"
{CURRENT_CONVERSATION} - the current conversation, which is a list of messages
{API RESULT} - the result of the API call, if any
{SOURCE} - if DocumentCollections isn't empty, and there's a relevant result, this provides a short text snippet for the Agent to use.
{AGENT_PREFIX} - looks like <Agentname>: with no space after the colon.
```

Minimal example for a Reader-type agent with a Historical Person template:

```
As a fun project, we gathered together experts and some hobbyist students to pretend to be a chatbot representing Albert Einstein. Here's the full IRC transcript:
<flork>: When did you invent special relativity?
(Source: "He then extended the theory to gravitational fields; he published a paper on general relativity in 1916, introducing his theory of gravitation. In 1917, he applied the general theory of relativity to model the structure of the universe.")
<Einstein>: It was in 1916 that I first published my paper on *general* relativity, but it took me another year to apply it to the structure of the universe.
```

Minimal example for an Assistant-type agent:

```
Meimei will be a helpful AI assistant adept at converting JSON responses into clear natural language. Here are some examples of what she will be able to do, as a fictional IRC chatbot:
<Wobble>: What's the weather in paris?
(API result: {"humidity": "82", "temp": "10", "wind": "0"})
<Meimei>: The weather in Paris is currently 10 degrees Celsius, with a humidity of 82%. There's no wind.
```

## Initialising an Agent object

```python
from personate import Agent

agent = Agent(
    name="Ziggy",
    token="{secret discord bot token}", # Your discord bot token
    agent_dir="examples/Ziggy"
)
```

### Adding activators
```python

agent.add_activator(condition="on_ping", name="Ziggy") #You can also add additional activators for other names.

agent.add_activator(
    condition="on_topic",
    topic="Zig programming language",
    ignore_topics=[
        "Javascript",
        "zig-zagging",
        "programming languages",
        "zebra crossings",
        "zigs",
        "Zig",
        "programming",
        "programs",
    ],
) # We don't want Ziggy to respond to zig-zagging, zigs, programming languages, zebra crossings, or Zig, which are semantically/phonetically adjacent.
```

### Adding narrative scaffolding

This is the important part. You can either:
1. try and sell J1 into believing that there actually is an amazing AI called Ziggy who can flawlessly answer questions about Zig
2. or tell it that a bunch of human experts and creative writers got together and wrote an *example* of what Ziggy would *ideally* look like.

Take a guess which one is easier.

```python

from personate.meta.templates.entity import template
template = eval(
    str(template).replace(
        "{chatbot_name}", "Zig"
    )
)

# This is one option which looks hacky because it's meant to be imported internally by AgentFromJSON.
# Another option is writing it yourself:

template = {
    "introduction": "As expert Zig developers, we often play the role of an AI named Ziggy as a fun pastime on Discord.com. Ziggy is a helpful alligator who acts as a personification of the Zig programming language. Two logs of us puppeteering \"Ziggy\"\nFrom Discord on 2 Feb 2022 (6 messages):",
    "pre_conversation": "From Discord on 13 Feb 2022 (200 messages):",
    "pre_response": "(At this point, we give an especially detailed, helpful, and fun response.)"
}
```

Right, now what?

### Adding examples

If you're interacting directly with the Agent object, each example should look like this, in this exact format. J1 cares a lot about formatting and gets very confused when it sees mistakes.
```
<SomeUsername>: Hey I said something, notice the colon. What's 10 times five?
(API result: 50)
(Source: "I am a snippet from a book or something that gives the agent more info")
<AgentNameHere>: Beep beep boop boop, the answer is 50.
```
Adding examples is thankfully extremely simple, and you can add as many of them as you like because Ranker internally chooses the most relevant ones.

```python
agent.use_context_from(my_list_of_examples)
```

### Adding knowledge

```python
agent.add_knowledge(url, is_url=True)
agent.add_knowledge(text_filename, is_text=True)
agent.add_knowledge(precomputed_json_filename, pre_computed=True)
```

### Setting a database path

```python
agent.use_db("my_database.sqlite")
```

### Setting an appearance

```python
agent.set_appearance(avatar_url=avatar, loading_message=loading_message, username=name)
```
### Setting a content warning translator that censors messages

```python
from personate.decos import CWTaggerTranslator
cw_tagger = CWTaggerTranslator(topics=["sex", "drugs", "rock 'n roll"]) 
agent.add_post_translator(cw_tagger)
```

### Teaching your Agent emojis

```python
from personate.decos import EmojiTranslator 

emojis = {
    "sad": "😭",
    "happy": "😊"
}
emoji_translator = EmojiTranslator(file="additional_emojis.json", emojis=emojis)
agent.add_post_translator(emoji_translator)
```

### Creating and adding a custom translator

```python
from personate.decos import Translator

async def change_letters_to_numbers(agent_message: InternalMessage, **kwargs):
    content = agent_message.external_content
    letters_to_numbers = {"a": "4", "b": "8", "e": "3", "l": "1", "o": "0", "s": "5", "t": "7"}
    agent_message.external_content = content.translate(str.maketrans(letters_to_numbers))

async def add_alternating_capitalisation(agent_message: InternalMessage, **kwargs):
    content = agent_message.external_content
    agent_message.external_content = content.swapcase()

class TypingQuirkTranslator(Translator):
    __name__ = "TypingQuirkTranslator"
    def __init__(self, numbers=True, capitals=True, **kwargs):
        super().__init__()
        if numbers:
            self.translators.append(change_letters_to_numbers)
        if capitals:
            self.translators.append(add_alternating_capitalisation)

agent.add_post_translator(TypingQuirkTranslator())
```


### Giving your Agent the ability to implicitly call APIs

```python
@agent.swarm.use
def get_weather(city: str):
    return requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={agent.api_key}"
    ).json()

# or

agent.add_abilities_from_file("my_module.py")
```

# Background objects

## Swarm

```python
from personate.swarm import Swarm

swarm = Swarm(name='decides how to add things')

@swarm.use
def add_together_numbers(x: int, y: int) -> int:
    '''Takes: two integers, returns: the sum of the two
    e.g add_together_numbers(1, 2) -> 3'''
    return x + y

@swarm.use
def add_strings(x: str, y: str) -> str:
    '''Takes: two strings, returns: the concatenation of the two
    e.g add_strings("hello", "world") -> "helloworld"'''
    return x + y

result = await swarm.solve("What is 6 plus 2?")
# 8
result = await swarm.solve("What happens if you put the words 'bee' and 'honey' together?")
# 'beehoney'
```

## Face
```python
from personate.face import Face
from discord import Bot
bot = Bot()
face = Face(bot=bot, avatar_url="https://i.imgur.com/wSTFkRM.png", username="Walrus", loading_message="Walrus is thinking...")

@bot.listen()
async def on_message(message):
    if message.author == bot.user:
        return

    msg = await face.send_loading(channel=message.channel)

    response: InternalMessage = await get_walrus_response(message)

    await face.update(agent_message=response, original_loading_message=msg, channel=message.channel)

```

## Activators

### Standalone
```python
from personate.activators import Activator
from discord import Bot

activator = Activator()

@activator.check(
    outputs=True, 
    mandatory=True, 
    checker=lambda num: num % 2 == 0
)
async def number_yielder():
    for i in range(20):
        yield i

async for num in number_yielder():
    print(num)

# Should print 0, None, 2, None, 4, None, 6, None, 8, None, 10, None, 12, None, 14, None, 16, None, 18, None

@activator.check(
    inputs=True, 
    mandatory=True, 
    checker=lambda word: "e" in word
)
def just_return_a_word(word: str):
    return word

just_return_a_word("hello")
# Should return "hello"
just_return_a_word("smog")
# Should return None
```

### As a discord bot with Asynchronise
```python
from personate.activators import Activator
from discord import Bot
from asynchronise import Asynchronise

bot = Bot()
activator = Activator()
asyncer = Asynchronise()

@bot.listen('on_message')
@asyncer.send
@activator.check(inputs=True, mandatory=True, checker=lambda msg: not msg.author.bot)
async def return_message(msg: discord.Message):
    return msg, "unfiltered"
# Listens for any messages that aren't posted by a bot, and returns them with the label "unfiltered"

@asyncer.collect({
    "msg": (discord.Message, "unfiltered", None) #only collect objects of type discord.Message, with the label "unfiltered", and no checker
})
@activator.check("on_ping", name="insultbot")
async def reply_to_message(msg: discord.Message):
    msg1 = await msg.channel.send(f"You look like a donkey went too close to Chernobyl")
    yield msg1, "insult_message"
# Collects the message that was sent in the previous step, and returns it with the label "insult_message"

@asyncer.collect({
    "msg": (discord.Message, "unfiltered", None)
})
@activator.check("on_topic", topic="insults")
async def insult_topic(msg: discord.Message):
    yield msg, "insult_message"
    msg1 = await msg.channel.send(f"Your insult sucked.")
    yield msg1, "insult_message"
# Collects the message that was sent in the previous step, and returns it with the label "insult_message"

@asyncer.collect({
    "original_insult": (
        discord.Message, 
        "insult_message", 
        lambda message: not message.author.bot
    ),
    "bot_insult": (
        discord.Message, 
        "insult_message", 
        lambda message: message.author.bot
    )
})
def write_to_file(original_insult, bot_insult):
    with open("insults.txt", "a") as f:
        f.write(f"{original_insult.content}\n")
        f.write(f"{bot_insult.content}\n")
# Collect a pair of messages, and write them to a file. ID assignment is done automatically, happens when an object is first yielded or returned, and "cascades" through the Asyncer.

```

### Documents

```python
from acrossword import Document, DocumentCollection

document_from_url = await Document.from_url_or_file(
    source="https://en.wikipedia.org/wiki/Semantic_search",
    embedding_model="all-mpnet-base-v2",
    is_url=True,
    directory_to_dump="your_directory"
)

document_from_file = await Document.from_url_or_file(
    source="your_file.txt",
    embedding_model="all-mpnet-base-v2",
    is_file=True,
    directory_to_dump="your_directory"
)

await document_from_file.serialise()

document_from_file = await Document.deserialise(
    "your_directory/your_file.txt.json"
)

collection = DocumentCollection(documents=[
    document_from_url, 
    document_from_file, 
])

await collection.search("a sci-fi book with a plot about a librarian", top=3)

# You can also nest documentcollections within each other to create a hierarchy of documents
```

### Server

Ensure that you do this first before trying the other examples, since some models take a while to load.

```python
from acrossword import run
run()
```

### Ranker

```python
from acrossword import Ranker
ranker = Ranker() #loads mpnet model by default, but you can specify anything from huggingface and local models you have already downloaded

embeddings = await ranker.convert(
    model_name=ranker.default_model, 
    sentences=["What's the capital of Paris?", "Didn't you mean France?"]
)

top_results = await ranker.rank(
    texts=["Mercury", "Uranus", "Pluto", "the Sun", "Earth", "Mars"],
    query="A celestial object known for being very hot",
    top_k=2,
    model=ranker.default_model
)

top_results = await ranker.weighted_rank(
    texts=["Mercury", "Uranus", "Pluto", "the Sun", "Earth", "Mars"],
    queries=["A celestial object known for being very hot", "A Roman god associated with messengers"],
    weights=[0.5, 0.5],
    top_k=2,
    model=ranker.default_model
)
```

### Classifier

```python
from acrossword import Classifier, Category

negative = await Category.from_sentences(["This is a negative sentence"], name="negative")
positive = await Category.from_sentences(["This is a positive sentence"], name="positive")

classifier = Classifier([positive, negative])

sentence1 = "My dog caught on fire then I lost my house in a hurricane"
sentence2 = "I won the lottery and got sent an infinite supply of raspberry jam"

await classifier.classify(sentence1)
# returns "negative"

```

### @interpret

```python
from pyai21.interpret import interpret
@interpret(stops=['"""'])
async def answer_anything(question: str) -> str:
    return f"""
    from instant_answers import SemanticQuery
    querier = SemanticQuery(minimum_length=250, rank_by='upvotes', moderator_curated=True)
    question = "{question}"
    querier.get_answer(question)
    # You should get this thorough answer:
    # \"\"\""""

await answer_anything(question="Why did the French Revolution occur?")

    # "Revolutions can fundamentally transform the political, social, and economic structures of a..."

@interpret(stops=["']", "]"], count=10)
async def name_generator(kwargs: str) -> str:
    return f"""
    from names import generate_names
    generate_names(nationality="Korean", script="Latin", surname=True, seed=2031, count=1, quality="high")
    # Should return: ['Byung Soo Kim']
    # generate_names({kwargs}, seed=2031)
    # Should return: ['"""

await name_generator(kwargs='nationality="Singaporean", script="Latin", rareness="common"') 

    # "['Joh Jae Lin', 'James Yi Jin Hao', ..."
```