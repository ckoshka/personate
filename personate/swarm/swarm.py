from typing import Dict, Callable, Any
import ast
from pyai21 import get
import inspect
from personate.utils.logger import logger
from personate.swarm.swarm_prompt import prompt


class Swarm:
    def __init__(self):
        self.abilities: Dict[str, Callable] = {}
        self.prompt = prompt

    def use(self, func: Callable) -> Callable:
        """This inserts a function into self.abilities, with the key as the function's docstring, and the value as the function itself"""

        if func.__doc__:
            self.abilities[func.__doc__] = func
        else:
            try:
                source = inspect.getsource(func)
                self.abilities[source] = func
            except Exception as e:
                self.abilities[func.__name__] = func
        return func

    def use_module(self, filename: str, register_all: bool = True) -> None:
        """
        This imports a module and adds all of its functions to self.abilities, but only those defined in the top-level. So if you're importing other functions into your module, it won't register those. You can turn this off by passing register_all=True.
        """
        import_module = __import__(filename)
        for name, obj in inspect.getmembers(import_module):
            if inspect.isfunction(obj):
                if not register_all:
                    if obj.__module__ == filename:
                        logger.debug(f"Registering {obj.__name__}")
                        self.use(obj)
                else:
                    logger.debug(f"Registering {obj.__name__}")
                    self.use(obj)

    async def solve(self, query: str) -> Any:
        """This uses ranker to evaluate which function is most suited to the query, calls it, and returns the result"""
        if not len(self.abilities.keys()) > 0:
            return
        from acrossword import Ranker

        ranker = Ranker()
        top_function_docstring = await ranker.rank(
            query="A Python function that would be able to solve this question: "
            + query,
            top_k=1,
            texts=tuple(self.abilities.keys()),
            model=ranker.default_model,
            return_none_if_below_threshold=True,
            threshold=0.1,
        )
        if not top_function_docstring:
            return
        func = self.abilities[top_function_docstring[0]]
        args: str = await self.get_arguments(
            query=query, top_function_docstring=top_function_docstring[0], func=func
        )
        result = await self.parse(args=args, func=func)
        return result

    async def parse(self, args: str, func: Callable) -> Any:
        """
        This parses the sourcecode as an ast.FunctionDef node to validate the args being provided.
        To actually create the appropriate arguments, it calls ast.parse on a string such as "func(a, b=b, *c, **d)", collects its arg nodes, and finally calls the actual function.
        """
        parsed_args: ast.Module = ast.parse(f"{func.__name__}({args})")
        logger.debug(f"Dumped tree: {ast.dump(parsed_args)}")
        arg_nodes: List[str] = [a.value for a in parsed_args.body[0].value.args]  # type: ignore
        keyword_nodes: Dict[str, Hashable] = {a.arg: a.value.value for a in parsed_args.body[0].value.keywords if isinstance(a, ast.keyword)}  # type: ignore
        # arguments_for_func: ast.arguments = ast.parse(inspect.getsource(func)).body[0].value.args
        # We could check for validity, but in practice the error will be propagated anyway.
        logger.debug(f"Parsed args: {arg_nodes}")
        logger.debug(f"Parsed keywords: {keyword_nodes}")
        if inspect.iscoroutinefunction(func):
            result = await func(*arg_nodes, **keyword_nodes)
        else:
            result = func(*arg_nodes, **keyword_nodes)
        return str(result)

    async def get_arguments(
        self, query: str, top_function_docstring: str, func: Callable
    ) -> str:
        func_name = func.__name__
        prompt = (
            self.prompt.replace("{query}", query)
            .replace("{documentation}", top_function_docstring)
            .replace("{name}", func_name)
        )
        args = await get(prompt=prompt, temp=0.55, stops=[")\n"], max=30)
        if isinstance(args, str):
            return args
        else:
            return args[0]
