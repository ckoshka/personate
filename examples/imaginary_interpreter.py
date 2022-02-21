from completions.interpret import interpret

# This interprets the results of fictional code examples

@interpret(stops=["\n", '"'], max=20, temp=0)
async def multiply(x: int, y: int) -> None:
    """def multiply(x: int, y: int) -> int:
        return x * y
    >> multiply(3, 12)
    # Returns "36"
    >> multiply({x}, {y})
    # Returns \""""

@interpret(stops=['"""'])
async def answer_anything(question: str, kwargs: str) -> str:
    return f"""
    from instant_answers import SemanticQuery
    querier = SemanticQuery({kwargs})
    question = "{question}"
    querier.get_answer(question)
    # You should get this thorough answer:
    # \"\"\""""

@interpret(stops=["']", "]"], size="j1-jumbo", count=10)
async def name_generator(kwargs: str) -> str:
    return f"""
    from names import generate_names
    generate_names(nationality="Korean", script="Latin", surname=True, seed=2031, count=1, quality="high")
    # Should return: ['Byung Soo Kim']
    # generate_names({kwargs}, seed=2031)
    # Should return: ['"""

@interpret(stops=['"'], size="j1-jumbo", temp=0.88)
async def question(answer: str) -> str:
    return f"""
    from huggingface import pipeline
    reverse_question_answerer = pipeline(model='bart-ask-questions', domains=["general_knowledge", "pop_references"])
    #This model will take an answer, and return a question that might have prompted it.
    reverse_question_answerer("{answer}")
    # Should return:\""""

import asyncio
async def run():
    q = await question("It's 42.")
    print(q) 
    # Output: How old is the donkey in Alice in Wonderland?
    # Which is uhhhh, an interesting response?
    q = await name_generator(kwargs='nationality="Singaporean", script="Latin", rareness="common"') 
    print(q)
    # Output: ['Joh Jae Lin', 'James Yi Jin Hao', 'Lee Kian Ham', 'Akira Sugiura', "Hendrie Choo', 'Liew Sien', 'Yeow Doo Hong", 'Brice P. Chia', 'Ma Siang Heng', 'Chua Wai Mun', 'Boon Soo Koh', 'Toh Chin Chye']
    q = await answer_anything(question="Why did the French Revolution occur?", kwargs="minimum_length=250, rank_by='upvotes', moderator_curated=True")
    print(q)
    # Some example outputs:
    #(1)
    # [Question #11174] Why did the French Revolution occur?
    #
    # Revolutions can fundamentally transform the political, social, and economic structures of a
    # country. Two widely-cited theories on revolutions begin with a discussion of the
    # French Revolution of 1789. According to the first theory, revolutions occur because
    # rising expectations among a dissatisfied population finally reach a breaking point,
    # leading to popular demand for governmental reform. The revolution of 1789 fits this
    # theory. Economists Robert Barro and Xavier Sala-i-Martin argued that there was a
    
    #(2)
    # The French Revolution was motivated by extreme unrest and a
    # population that suffered from extreme poverty. The causes of
    # the French Revolution can be traced to the 16th century,
    # during which time France underwent a series of changes
    # that began to strain relations between the rich and the poor.
    # These tensions led to the French Revolution in the late 18th
    # century.
    #
    # The revolutionary ideals of liberty and equality that emerged
    # from France's 1789 revolution also inspired leaders around the
    # world. The 1789 revolution began France's political
    # transformation from an absolutist monarchy to a republic.
    q = await multiply(4, 4)
    print(q)
    # Output: 16

16

asyncio.run(run())
