## Things that should be done in the near future
**META**
* Better organisation. I do not know how to manage an open-source library and it shows. Need help with this.
* Write a bash script that handles all of the set-up. Hell, you could probably automate the process of making keys with Selenium. Laziness Is Good.
* Other convenient ways of initialising Agents aside from Python scripting and JSON files.
* Figure out how to make the dependencies optional, while providing helpful error messages if you don't have them.
* Figure out how to make the SentenceTransformers library optional. It's a big library and if you try to install it on Replit, it will display a memory error. [Fast Sentence Embeddings](https://github.com/oborchers/Fast_Sentence_Embeddings) looks promising, but it's still very heavy on storage and kinda sucks at semantic search. This library is just network I/O and string manipulation glued together with simple NLP, it should be able to fit on a Raspberry Pi.
* Adding a metric shit ton of examples. Documentation is cool, and it would be great if there was some sprinkled for each function and class, but I don't read docs, I just look at examples. Maybe get J1 to come up with examples automatically.
* Show demo gifs or videos or some animated text thing so people know they're not being bilked.

**INTERFACES**
* It currently only works with Discord. That sucks. Not everyone is on Discord. The Agent and AgentFrame class should be rewritten to work with other platforms. A console version would be cool and easy.
* Fixing the slash commands on Discord (in personate.meta.inbuilt_commands). I want them to be message commands so we can apply them to individual Agents if there are multiple of them using the same bot account at the same time. Right now they don't work. 

**MEMORY**
* Agents should be able to write facts to their permanent memory, ideally as a Document. So should owners.

**FILTERS**
* Meanness filter based on Classifier from acrossword that detects agents being mean

**DOCUMENTS**
* An automated Stackoverflow scraper that can create Documents from answers.

## Things that should be done that are very cool and probably fun to program, but not essential
**APIS**
* Agents used to be able to "decide" which functions to call, and be able to call multiple functions in sequence while interpreting their responses. To implement that again, you would just need to:
    * Write examples of agents using functions like this ">>> funkyfunc(arg1, kwarg=kwarg)"
    * Then use the already-written AST-based interpreter in swarm.solve to get the result
    * And send it back to the AgentFrame 
    * And repeat this until the agent says something that isn't a command. This is hard because agents love calling commands. If you ask them to get the weather for Tokyo, they will also get the weather for Paris and London too. When I ask them to explain why they do this, they either say that they're curious or lie to me and say that there was a glitch and make up a fake Pythonic-looking error. That's why I decided not to put this on the final library.
* Dynamically-chosen goals for agents
* Give agents the ability to draft responses or think before they talk
* Routine class that causes agents to do stuff regularly like read the news and write a blog about it on Discord or whatever
* World class for RPGs
* A Rust port. That would be very very cool.
* A full rewrite of the library where everything is a function and completely modular