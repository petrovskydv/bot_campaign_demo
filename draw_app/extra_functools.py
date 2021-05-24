from functools import partial
import contextlib

__all__ = [
    'decorate',
    'suppress',
]


@contextlib.contextmanager
def decorate(context_manager, *args, **kwargs):
    """Wrap context_manager to use it as a function decorator."""
    with context_manager(*args, **kwargs):
        yield


suppress = partial(decorate, contextlib.suppress)
