from personate.utils.usernames import usernames

unames = usernames.splitlines()
import random


def username_generator() -> str:
    return random.choice(unames)
