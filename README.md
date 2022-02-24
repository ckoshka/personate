<img src="https://user-images.githubusercontent.com/48640397/154764793-154a3c99-6439-43b6-9d7e-09b8b2baf8aa.png" alt="drawing" width="500px" display="block" alignment="middle"/>
<img src="https://user-images.githubusercontent.com/48640397/154828805-160b7770-9460-43af-8e42-bf52af5fb08c.png" alt="drawing" width="500px" display="block" alignment="middle"/>

First, I want to save your time and help you decide whether you want to use this library. Click on whichever one describes you best.

- [🔧  I have a specific problem. **I'm looking for a library that solves it in a high-level way, without forcing me to consult reams of documentation, or adopt a whole new framework**](#problem)
- [☁️ I don't have a concrete problem, but **I'm dissatisfied with what I'm doing right now, and I'm looking for something that does it better / faster / less verbosely / etc**](#improvement)
- [✨ **I like playing with cool shiny AI tools** and I'm just idly shopping in the hope I might find more of them](#shopping)

If none of those describe you, here's the 30-second FAQ:

## Why does it exist?

* Gigantic language models exist. They are mysterious, infamously unreliable, very bad at multitasking, sometimes spout Nazi propaganda, and 99% of the time, they don't do what you tell them to. They're also incredibly good liars.

Personate allows you to make these language models:
* Reliable and repeatable
* Composable into larger complex systems
* Parallelised and asynchronous
* Highly configurable
* Honest
* And non-toxic

Without:

* Expensive retraining
* A deep understanding of machine learning
* Changing your existing code too much

## What does it let me do?

Anywhere you need human intelligence on tap, you can drop decorators from Personate into your code, and get it. Here are some things I've done with Personate:

* Created a personification of the Zig programming language called Ziggy that answers questions about itself by reading its English manual, in Mongolian
* Recreated Alan Turing from his Wikiquotes page, quizzed him on his published papers, then taught him how to use custom Discord emojis
* Made a bot that can simply read the docstrings for my functions, call the appropriate API, and parse the raw JSON response into natural language
* Made an asynchronous swarm that interprets the images I post, and writes poetry inspired by them, in my style

(All of these are in the ``examples`` folder, and you can play around with them)

## What does it look like in practice?

This is all it takes to instantiate a non-toxic, knowledgeable chatbot that keeps track of thousands of conversational threads, has a consistent personality, and consults hundreds of pages of documentation in a tenth of a second:

```python
from personate import Agent
from personate.completions import default_generator_api

agent = Agent(
    name="Ziggy",
    token="{secret discord bot token}",
    generation_api=default_generator_api,
    should_read=True,
    agent_dir="examples/Ziggy"
)

agent.add_activator(
    condition="on_topic",
    topic="Zig programming language",
    ignore_topics=[
        "zig-zagging",
        "programming languages",
        "zigs",
    ],
)

agent.add_activator(condition="on_ping", name="Ziggy")

agent.set_appearance(avatar_url="ziggy.png")

agent.use_template("examples/Ziggy/template.txt")
agent.use_context_from("examples/Ziggy/examples.txt")
agent.add_knowledge_directory("examples/Ziggy/knowledge")

from personate.translators import LanguageTranslator
agent.add_pre_translator(LanguageTranslator())
agent.add_post_translator(LanguageTranslator())

agent.run()
```

This is all you need to make an infinitely customisable name generator for your RPG.

```python
from personate import interpret

@interpret(stops=["']", "]"])
async def name_generator(kwargs: str) -> str:
    return f"""
    from names import generate_names
    generate_names(nationality="Korean", script="Latin", surname=True, seed=2031, count=1, quality="high")
    # Should return: ['Byung Soo Kim']
    generate_names({kwargs}, seed=2031)
    # Should return: ['"""

await name_generator(kwargs='nationality="Singaporean", script="Latin", rareness="common"')
```

This is how you can turn your functions into fully coordinated, event-driven async generators that yield their results mid-step, letting other functions (both synchronous and asynchronous, generators or non-generators) use them immediately.

```python
from personate import swarm

swarm = Swarm()

@swarm.send
async def do_expensive_multistep_stuff():
    flour: Ingredient[Flour] = await go_to_the_store()
    yield flour

    egg: Egg = await get_eggs(variety="scrambled")
    yield eggs, "scrambled"

    egg: Egg = await get_eggs(variety="raw")
    yield eggs, "raw"

    milk: Ingredient[Milk] = await get_milk()
    yield milk, "liquid"

@swarm.collect({
    "egg": (Egg, "scrambled", lambda egg: egg.weight > 100)
})
def eat_egg(egg):
    # This won't block the event loop 
    time.sleep(10) 
    print(f"Yummy!")
    
@swarm.send
@swarm.collect({
    "orders": (int, "customer_order", None),
    "flour": (Flour, None, lambda flour: flour.type == "rye"),
    "liquid": (None, "liquid", lambda liquid: hasattr(liquid, "stir"))
})
async def make_dough(orders, flour, liquid):
    # I don't actually understand how making bread works, sorry to any bakers out there.
    for order_num in range(orders):
        await liquid.stir()
        dough = await flour.mix(liquid)
        yield dough, order_num
    
```

And this is all it takes to allow your chatbots to use arbitrary Python functions:

```python
@swarm.use
@apis.get("wordsapiv1.p.rapidapi.com")
def info_for_word(info_type: str, word: str) -> str:
    '''Returns dictionary information for a given word'''
    return f"https://wordsapiv1.p.rapidapi.com/words/{word}/{info_type}"
```


# So you have a problem
<a name="problem"></a>
So you have a problem and you're looking for a library that solves it in a high-level way with the minimum possible hassle. Instead of trying to dazzle you with buzzwords, I'm just going to:

1. Tell you what problems it can solve
    - starting with the general, narrowing down to the specific.
2. Show you how it solves it
    - with easily copy-pastable examples
3. And lastly, give you results, so you can evaluate whether it's a good fit for you.

Then I'll do the normal Github repository stuff.


# **Quickstart**

```bash

```

**Things you can do with this library include:**
* Create a personification of the Zig programming language that answers questions about itself based off its English manual ... in Mongolian
* Resurrect Alan Turing and ask him about any of his published papers ... then teach him how to use custom Discord emojis
* Use a single @decorator to give your bot the ability to call a weather forecast API ... then parse the raw JSON data into natural language
* Make an asynchronous swarm that interprets the images you post ... and writes poetry inspired by them, in your style
* Create chatbots ... that make other chatbots
* And a lot, lot more.

- Currently the bottleneck is documentation, but I will have a library with demos up within the next week
