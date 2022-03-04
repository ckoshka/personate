from acrossword import Ranker


class SemanticList(list):
    """A list with an additional method called reorder that takes:
    - query: a string to rank the list's contents by"""

    def set_maximum(self, maximum: int) -> None:
        self.maximum = maximum

    def set_delimiter(self, delimiter: str) -> None:
        self.delimiter = delimiter

    def set_ranker(self, ranker: Ranker) -> None:
        self.ranker = ranker

    async def reordered(self, query: str) -> list:
        contents = [str(item) for item in self]
        ranked = await self.ranker.rank(
            texts=tuple(contents),
            query=query,
            top_k=999999,
            model=self.ranker.default_model,
        )
        return list(reversed(ranked[: self.maximum]))

    def __str__(self):
        return self.delimiter.join(self[: self.maximum])

    def __repr__(self):
        return self.delimiter.join(self[: self.maximum])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.maximum = 5
        self.delimiter = "\n"
        self.ranker = Ranker()
