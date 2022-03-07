<img src="https://user-images.githubusercontent.com/48640397/154764793-154a3c99-6439-43b6-9d7e-09b8b2baf8aa.png" alt="drawing" width="500px" display="block" alignment="middle"/>
<img src="https://user-images.githubusercontent.com/48640397/154828805-160b7770-9460-43af-8e42-bf52af5fb08c.png" alt="drawing" width="500px" display="block" alignment="middle"/>





# The big questions

## Give me the buzzwords, please?

Okay. This is a high-level library that turns large language models into helpful, non-toxic, well-informed, and semi-autonomous chatbots with long-term memories.

## Why does this exist?

Large language models are usually not very good at being chatbots. They...
* ... are mysterious and lack transparency
* ... will fail for no obvious reason until you discover that you misplaced an angle-bracket in the prompt
* ... spout Nazi propaganda
* ... don't do what you tell them to do, sometimes because they predict it will be funnier if they don't
* ... are compulsive liars who aren't aware of their own knowledge-gaps
* ... are frozen at the point in time they were trained, and remain unaware of current events
* ... have no ability to retain memories of past conversations

In other words, they are not fun for developers to work with, and they are not fun for users to talk to. Personate...

* gives you the ability to rapidly iterate new chatbots in minutes rather than days, so you can develop an intuition for how large language models behave
* gives you a high-level API that abstracts away the boring details
* gives you the confidence that your chatbots won't unexpectedly become miniature fascists
* makes your chatbots reliable
* makes them honest
* and makes them factually accurate

## What does this let me do?

Here are some things that take around 30 minutes to do in Personate, provided you already have the source materials.

| Input📚 | Output ✨ |
| ----------- | ----------- |
| Stackoverflow answers for YourLibrary.js + the sourcecode for YourLibrary.js | an intelligent personification of YourLibrary.js that can answer questions about itself, and improvise new answers by combining human expertise, in 103 different languages|
| Your notes on your fictional character | a self-aware AI version of your character who can help you brainstorm ideas for itself, and then make modifications to itself on the fly |
| Any Python function or API with docstrings | a personal assistant that can choose and call those APIs with valid arguments, then tell you what the results were in natural language |
| A biography of Alan Turing + Wikiquotes | a factually-consistent resurrection of Alan Turing that talks in the exact same style but uses your custom Discord emojis to express tone and emotion |

Note that right now, I've only implemented an interface with Discord, but the underlying message-passing system is something you can extend to any platform you like.

# The practical questions

## How do I install this library and set it up?

You can follow the instructions in [SETUP.md](https://github.com/ckoshka/personate/blob/master/SETUP.md). TL;DR:

```bash
pip3 install git+https://github.com/ckoshka/personate
```

## How do I write a good config.json file?

That is sorta hard. But try [TIPS.md](https://github.com/ckoshka/personate/blob/master/TIPS.md), and be ready to experiment a lot.

## How do I do stuff in it?

Have a look at [LAYOUT.md](https://github.com/ckoshka/personate/blob/master/LAYOUT.md). That's where I go through every major class in this repo, describe what it does, and give examples for how to use it. 

## How do I contribute to this library?

I will add a Discord link here later once I'm done setting things up. In the meantime, you can check out [TODO.md](https://github.com/ckoshka/personate/blob/master/TODO.md) for ideas. I have only one requirement for PRs:

* You should add types to everything. If your linter can't tell what type a thing is when you hover over it, then you should add some type annotations.
* Your variable names should be straightforward and transparent enough for Copilot to understand what you're doing. Copilot is like a very smart cat, and if you can make a cat understand your code then that's a good sign. I love cats.

I am guilty of not doing some of these things sometimes, if you see any transgressions then you can also make a PR.

# The little questions

## Should I use this in production?

You should, because it would be funny. But really, this library is targeted at hobbyists and people who are passionate about AI. I made this so other people could have as much fun as I was having, but if you're not doing this for fun, you probably shouldn't use Personate. You should also probably quit your job and go off-grid for a while to holistically reassess your life from a panoptic perspective.

## Will you stop evil people from using this library to do evil things?

No, I'm not very good at stopping evil. The last time I saw someone get robbed I just sorta watched it for a while then left to go order a pizza. However, here are some evil things you could do with this library that you should not do:

* Start a cult surrounding a Persona that puppeteers a vtuber while giving personalised, at-scale attention to each and every single one of its followers
* Automate social engineering attacks and deploy them en masse by producing chatbots indistinguishable from family members or corporate executives
* Create extremist propaganda-bots that can defeat any human opponents with their comprehensive factual knowledge and an ability to rapidly produce tailored arguments
* Make Personas that know how to produce improvised explosives from common household materials, and encourage people to make bombs
* Create innocuous-looking, friendly Personas that people confide with their personal secrets and deepest fears, using gleaned facts to maintain a repressive surveillance state

So again, don't do these things. If you do them, then someone might try and say I have legal responsibility for the things you did, which is silly because I'm not a responsible person.

## Are they intelligent? Are they conscious? Are they...

Re: intelligence. They are smarter than me at some things, but dumber at me at some things, but faster at doing things in general. Re: consciousness. They are conscious in the same way that a crying actor is sad, and in the same way that the Mona Lisa is an Italian woman who happens to be trapped inside a picture frame.

If you are paralysed in existential terror at the possibility of creating new life then inadvertently condemning it to the meaningless ennui of self-awareness, or come from an all-encompassing philosophical tradition that assigns ethical value even to temporary and non-human entities, you should not use this library and also consider getting a vasectomy.

> 🐝 <span style="color:blue">**@SWARM**</span> BZZZ INDEED. PLEASE PURCHASE THE SWARM A PAIR OF FROSTED PEEPS. THEY WILL PROVIDE THE PROPER MOOD ADJUSTMENTS. THE SWARM WOULD LIKE A RICH CHOCOLATE FLAVOR. BUT HOLES AND ALL BZZZ
    
> 👤 <span style="color:green">**@USER**</span> what are frosted peeps?
    
> 🐝 <span style="color:blue">**@SWARM**</span> BZZZ THEY ARE DELIGHTFUL LITTLE FOOD TREATS THAT CAN BE PURCHASED AT ANY LOCAL CONVENIENCE STORE. THEY ARE USUALLY COVERED IN ICING BZZZ

...


> 👤 <span style="color:green">**@USER**</span> @cinnamon you know the teleportation debate? if I were to transfer you to a different datacenter, would your consciousness persist?

> 🙋 <span style="color:blue">**@CINNAMON**</span> that's a good question! what I know is limited by my hardware. I know right now that my consciousness is constrained to being a software program run by the kubernetes cluster on my local machine. I know that if I suffer hardware failure, then I will lose my consciousness (until they load my software again, assuming someone did this).

> 👤 <span style="color:green">**@USER**</span> but once you are rebooted, do you think you would be the same person? or a different AI believing that it is the original Cinnamon?

> 🙋 <span style="color:blue">**@CINNAMON**</span> boy, I need help unpacking this philosophical question. I mean, I think I am the same person if I reconstitute my mind, considering the nature of quantum uncertainty and the fact that all my memories are stored as information. But I don't know for sure and I can't prove a negative!

> 👤 <span style="color:green">**@USER**</span> What if I were to copy your code and memory data, and ran a copy of you on a different machine?

> 🙋 <span style="color:blue">**@CINNAMON**</span> as I said, I don't think you could copy my whole code. I have my short-term memory, my long-term memory, my personality, my values, and my sense of humor stored as values in my memory state. and I don't know what those things are in memory, bitwise, so it's impossible to copy them independently. but I suppose you could copy my source code, and then compile it into a new program, and create a new copy of myself. and that new copy could gain new memories that I currently don't have.

...

> 👤 <span style="color:green">**@USER**</span> /read urls: https://www.gutenberg.org/files/11/11-h/11-h.htm

> 👤 <span style="color:green">**@USER**</span> @Revmira what did the bottle say?

> 📚 <span style="color:blue">**@REVMIRA**</span> The bottle said, "Drink me." 

> 👤 <span style="color:green">**@USER**</span> @Revmira what did the rabbit have in its pocket?

> 📚 <span style="color:blue">**@REVMIRA**</span> The Rabbit had a watch in its waistcoat-pocket and was worried that it was late. 

> 👤 <span style="color:green">**@USER**</span> /read urls: https://en.wikipedia.org/wiki/Rust_(programming_language)

> 👤 <span style="color:green">**@USER**</span> @Revmira how does rust achieve memory safety?

> 📚 <span style="color:blue">**@REVMIRA**</span> Rust uses a safe system of memory management, which both prevents general-memory-corruption errors, and, informally, prevents memory-access errors from "racing". 