"""ACME utilities."""
from typing import Callable
from typing import Dict
from typing import Any


def map_keys(dikt: Dict[Any, Any], func: Callable[[Any], Any]) -> Dict[Any, Any]:
    """Map dictionary keys."""
    return {func(key): value for key, value in dikt.items()}
