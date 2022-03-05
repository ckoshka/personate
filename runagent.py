from personate.meta.from_json import AgentFromJSON
import os
import sys

# fetch the json filename from the first argument
try:
    filename = sys.argv[1]
    agent = AgentFromJSON.from_json(filename)
    agent.run()
except IndexError:
    print("Please provide a json filename as the first argument")
