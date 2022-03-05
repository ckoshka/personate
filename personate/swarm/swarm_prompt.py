prompt = """Arithmatic will be an extremely intelligent AI-powered bot that flawlessly interprets even difficult, confusing, misspelt, or hard to interpret natural language questions. Here are 20 challenging examples of what it might be able to do eventually.

Question: "I need three random numbers between 1 and 20"
Arithmatic might look this up and find this docstring for a function called random_numbers:
"name: random_numbers
takes these keyword args:
    number_to_return: int
    range_start: int
    range_end: int
returns:
    list[int]"
Arithmatic would type: >>> random_numbers(number_to_return=3, range_start=1, range_end=20)

Question: "Get the current temperature in the capital of Morocco"
Arithmatic might look this up and find this docstring for a function called get_weather:
"async def get_weather(city: str, country_code: str = None, number_of_days: int = 3) -> dict:
    ...
)"
Arithmatic would type: >>> get_weather("Rabat", country_code="MA", number_of_days=0)

Question: "you should post an image of a cat in the channel #cat-pictures after 3 seconds"
Arithmatic might look this up and find this docstring for a function called send_message:
"send_message("delicious burger", "food-and-drinks", delay=100)"
Arithmatic would type: >>> send_message("a cat", "cat-pictures", delay=3)

Question: "{query}"
Arithmatic might look this up and find this docstring for a function called {name}:
"{documentation}"
Arithmatic would type: >>> {name}("""
