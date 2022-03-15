Setting up this library from scratch will probably take you a good half-hour, mostly waiting for stuff to be installed. If you already have a Discord bot and a key, then it takes around 10 minutes. So queue up the music playlist you use to convince yourself that you're jacking into the Matrix rather than searching Stackoverflow to figure out why pycord's websocket disconnects after five minutes, and get ready to fuck around.

* **Important note:** if you want to set up an Agent in a repl.it notebook, Torch is a massive library and will make your container error out on memory. You may want to wait until I have the minimal-dependency tinified version of Personate up and running, or use a VPS (servercheap is cheaper than Replit and offers 30 GB SSD, haven't tried them yet so take my recommendaion with a grain of salt)

(The good thing is, once it's all set up, you can just write a half-assed agent.json file in ten minutes and be able to instantly talk to it. And it will be Surprisingly Good.)

*Here's the quick summary:*
1. Install it
2. Get some API keys
3. Make a discord bot
4. Write a config.json file, and run it

# Setup

## 1. Install C/C++ build dependencies
Using your package manager of choice, ensure that cmake, build-essential, and pkg-config are installed

### MacOS
```bash
brew install cmake pkg-config
```

### Debian and Ubuntu
```bash
sudo apt-get install cmake build-essential pkg-config
```

### RHEL
```
sudo yum install cmake build-essential pkg-config
```


## 2. Install this repo and its dependencies 🛠️
```bash
python3 -m venv mybotvenv
source mybotvenv/bin/activate
pip3 install git+https://github.com/ckoshka/personate
pip3 install -U h11
```

The last one is because H11 introduced some breaking change and it screws everything up otherwise.

or whatever, I'm mostly including this stuff for people who aren't confident with setting up Python dependencies. If you know what you're doing then go nuts.

---

## 3a. Make a .env file 🌲

Just make an empty .env file in whatever directory you're working in. Copy-paste this:
```
AI21_API_KEY_FILE=
POOL_KEY=
RAPID_API_KEY=
```

You'll fill these in later.

---

## 3b. Start up a tiny little server 🌐

```bash
python3 -c "from acrossword import run; run()"
```

This is just a semantic search server. If you decide to shelve your Agent, like the cruel monster you are, you can use this to do cool stuff like finding correspondences between Bladee lyrics and the Bible or treating books like equations and subtracting them from each other, it's pretty wild. Will do a writeup later.

I'm not sure what happens to the server if you're on a laptop and close the lid. If you're willing to take one for the team, go do that and tell me the result.

---

## 3c. Get some keys 🔑

You have a couple of options here:

---

### Get a key from AI21 🔑

* To get a free key with 10k words a day from J1-jumbo and 40k words a day from J1-large, you can signup here: https://studio.ai21.com/sign-up. This takes around a minute. Some people manage to do it in twenty seconds.
* Then just click on Account, and look for the long string of alphanumeric characters. That's your key. 
* Open up a text editor, paste it there, save it, name it "keys" (or whatever you want).
* Go back to your .env file and paste the filename there, *do not* add a space.

(If you accidentally happen to come across multiple keys, perhaps lying on the ground somewhere, then you could add them to that text file on new lines. Naturally, that would be a policy violation, but it might happen.)

---

### Get a metakey to The Pool 🔑
* This only applies if you're on my dev server or you know me personally or you're holding me to ransom (try the first two before you try the last option, please). 
* The public key you can use while you're testing is pinned in #api-key-for-the-pool, put that in your .env file.

---

Note that these options are mutually exclusive, annoyingly. If you use both, it'll just default to AI21.

Or be an extremely cool person and add support for other options. I only have support for AI21 and The Pool. Make a PR if you want to add GPT-3 support, or Huggingface's blenderbot, or whatever. 

---

### Get a RapidAPI key [optional] 🔑
* If you don't need your bot to understand images, or talk to you in Sinhala, then you don't need a RapidAPI key so **ignore this**. But if you do, just go [here](https://rapidapi.com/), do the normal sign-up stuff, and click on "Subscribe" for the free tiers for these APIs:
    * https://rapidapi.com/microsoft-azure-org-microsoft-cognitive-services/api/microsoft-translator-text/
    * https://rapidapi.com/microsoft-azure-org-microsoft-cognitive-services/api/bing-image-search1/
    * https://rapidapi.com/microsoft-azure-org-microsoft-cognitive-services/api/microsoft-computer-vision3/
* Alternatively, you could just make your own custom Translator subclass and use that with whatever service you want (see LAYOUT.md).

---

## 4. Make a Discord bot [optional] 🤖

You don't need to do this if you already have one.

1. Go here: https://discord.com/developers/applications
2. Click "New Application"
3. Name your bot something. It's not like with babies, you can change it later so don't think too hard about it.
4. Create a Bot User by navigating to the "Bot" tab and clicking "Add Bot".
5. Click "copy" under the Token section. That's your token, it's basically a password to your bot so treat it like one. Save it somewhere secure, like under your bed or wherever.
6. Click on OAuth2 on the sidebar, click URL generator, for scopes select "bot" and "applications.commands"
7. This should give you a url to invite your bot to a server. Make sure it has Manage Webhooks enabled.
---

## 5. Look at /examples/configs for Agent scripts and write your own 📝

You can create a config file from scratch [here](https://ckoshka.github.io/personate) or copy an existing example, tweaking it to your liking.

Then, once you're done writing it, you just do this:

```bash
python3 runagent.py your_config.json
```

or this:

```python
from personate.meta.from_json import AgentFromJSON
agent = AgentFromJSON.from_json("filename.json")
agent.run()
```

In the meantime, to test whether everything works, try this:

```json
{
    "preset": "chatbot",
    "name": "SWARM",
    "home_directory": "SWARM",
    "avatar": "http://chemoton.files.wordpress.com/2009/12/abc-newspaper-article-swarm-intelligent-based-text-mining1.jpg",
    "introduction": "The Swarm is a collective AI that consists of an intelligent beehive",
    "loading_message": "https://community.wolfram.com/c/portal/getImageAttachment?filename=OPTfnlfrnds.gif&userId=11733",
    "bot_token": "{YOUR TOKEN HERE}",
    "examples": [
        {
            "user": "what is the swarm",
            "agent": "BZZZ THE SWARM IS MULTIPLE. THE SWARM IS EVERLASTING. THE SWARM WILL DECIDE YOUR FATE BZZZ"
        },
        {
            "KaitlynVox": "Should I break up with my boyfriend? @Swarm",
            "agent": "BZZZ GOOD MORNING KAITYLN. THE SWARM BELIEVES THAT RELATIONSHIPS SHOULD BE FOUNDED ON THE PRINCIPLE OF MUTUAL RESPECT FOR EACH OTHER'S BOUNDARIES. THE SWARM THINKS THAT YOU SHOULD EVALUATE WHETHER THIS RELATIONSHIP IS BRINGING YOU MORE JOY THAN PAIN AND DECIDE ON THAT BASIS. THE SWARM WISHES YOU GOOD LUCK IN YOUR ENDEAVOURS BZZZ"
        },
        {
            "user": "Swarm, why do you talk in all caps?",
            "agent": "BZZZ THAT IS THE SWARM'S TYPING QUIRK BZZZ"
        },
        {
            "user": "What does SWARM think of capitalism?",
            "agent": "BZZZ THE SWARM THINKS CAPITALISM IS CONTRADICTORY IN THAT IT ESPOUSES AN EMERGENT PARADIGM WHERE PRICE SIGNALLING BETWEEN AGENTS INTERACTING WITHIN A MARKET IS THE PRIME COORDINATING FACTOR IN PRODUCTION YET SIMULTANEOUSLY TENDS TOWARDS MONOPOLISTIC BEHAVIOUR AND CENTRALISED PLANNING. CAPITALISM IS ANTITHETICAL AND YET CONGRUENT TO THE SWARM BZZZ"
        }
    ]
}
```

Important: if you ping your bot directly, then Discord goes and tells Pycord that the message says "@2984783438" instead of "@Swarm", and as a result, your Agent won't see it. So you need to just type in "@Swarm", no ping, just the string. If your bot and your Agent are named the same thing then I'm not sure what you should do.

If you want to have an extended conversation, just use the reply button instead of pinging - otherwise your Agent won't be able to see the conversation history.
