from swarm.swarm import Swarm
from decos.classifier import Classifier
from activators.activators import Activator
from completions.interpret import interpret

swarm = Swarm(name="makes Costa Rica happier") # it is traditional to christen your swarm with a name that describes what it does. this is helpful if you have a metaswarm composed of many swarms, or if you enjoy playing god, you sick megalomaniac.

@swarm.at_start
@swarm.sender("article")
async def poll_for_articles() -> AsyncGenerator[Article, None]:
    """Checks for topics of interest."""
    while True:
        article: Article = await bbc.get_article()
        if article.topic == "South America":
            yield article

classifier = Classifier.from_dict(categories={"negative": ["This article is negative", "This is bad news"], "positive": ["This article is positive", "This is good news"]})

@swarm.receiver("article") # generally aim to describe objects as object-type + object-subtype + object-state. not needed here, but good idea generally.
@Activator.check(checker=lambda article: "Costa Rica" in article.text, mandatory=True, inputs=True, keyword="article")
async def costa_rica_article_summariser(article: Article = None) -> str:
    """Summarises relevant articles into a form that our swarm workers can read"""
    headline: str = pythy.summarise(article.text)
    category = classifier.classify(headline)
    if category == "negative":
        await swarm.send(source_type="negative_headlines")
    elif category == "positive":
        await swarm.send(source_type="positive_headlines")
    return headline

@swarm.receiver("positive_headlines")
@swarm.sender("reaction")
async def positive_reacter(headline: str = None) -> str:
    return "Yay! " + headline

@swarm.receiver("negative_headlines")
@swarm.sender("positive_headlines")
@interpret(max=300, stops=["\n", "Negative:"])
async def negative_news_spinner(headline: str = None) -> str:
    return f"""It's very easy to spin things to make them sound positive. Here are some events, reported by different media outlets as examples.

    Negative: Cute kitten gets brain tumour, 2 weeks left to live
    Positive: A win for ecological diversity: notorious bird-eating feline on the decline

    Negative: Global warming may have as much as 60% of Florida underwater by 2060
    Positive: Florida could become the world's biggest waterpark by 2060

    Negative: {headline}
    Positive:"""

@swarm.receiver("reaction")
async def costa_rica_toxic_positivity_astroturfer(reaction: str = None) -> None:
    await twitter.tweet(reaction)

swarm.print_chart()
swarm.run()
