### Why does this folder exist?

* I had to make a lot of decisions like "How much of the underlying API should I expose?" and tradeoffs like customisability vs simplicity. 
* Those were annoying and I still think the best thing to do is probably to fork this repo and fuck around with things in it until they look like what you want. This contains a bunch of examples for how to do that
* I think the Agent class is bloated and slow. Actually the whole library is pretty bloated. A lot of the time I just went "hey, wouldn't it be cool if this was an object?" and just did it without thinking too hard. 
* So this contains a bunch of minimal examples for how to set up an Agent from scratch.

### What's in it?
* agent_from_scratch.py >> what it says on the tin, shifts to emphasising decorators over objects which I think is cooler. It's also separated from Discord, which means you can just cut out the Pycord stuff and put it on a website or on Telegram or whatever
* rpg_functions.py >> this has a bunch of convenience functions for making RPGs, like generating a set of items that might be found in a location, creating characters, etc.