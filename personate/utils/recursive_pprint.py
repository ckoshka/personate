from rich.pretty import pprint
from typing import Optional, Any
import jsonpickle
import ujson as json


def recurse_print(obj: Any):
    """Recursively prints a nested object, with a maximum depth of 3."""
    serialised: Optional[str] = jsonpickle.encode(obj, max_depth=2)
    if serialised:
        pprint(json.loads(serialised))


def recurse(obj: Any) -> Optional[dict]:
    serialised: Optional[str] = jsonpickle.encode(obj, max_depth=2)
    if serialised:
        return json.loads(serialised)
    else:
        return None
