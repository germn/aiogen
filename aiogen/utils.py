from typing import List, Iterable
import asyncio as aio
import unittest
from functools import wraps

from aiogen.agenerator import AsyncGenerator


# SIMPLE EVENT LOOP:
def run_until_complete(coro):
    """Run new event loop until coroutine complete."""
    loop = aio.new_event_loop()
    aio.set_event_loop(loop)
    loop.set_debug(True)
    try:
        loop.run_until_complete(coro)
        loop.run_until_complete(AsyncGenerator.cleanup())
    finally:
        loop.close()


# TESTS:
class AsyncTestCase(unittest.TestCase):
    """TestCase to run all coroutine functions in class in separate event loop."""
    @classmethod
    def setUpClass(cls):
        # Decorator to create plain function from coroutine:
        def run_in_loop(coro_func):
            @wraps(coro_func)
            def wrapper(*args, **kwargs):
                run_until_complete(coro_func(*args, **kwargs))
            return wrapper
        # All coroutines should be executed in event loop:
        names = unittest.TestLoader().getTestCaseNames(cls)
        for name, obj in vars(cls).items():
            if (name in names) and aio.iscoroutinefunction(obj):
                setattr(cls, name, run_in_loop(obj))


def extract_tests(item) -> Iterable[unittest.TestCase]:
    """Extract TestCase instances from item (usually TestSuite)."""
    if isinstance(item, unittest.TestCase):
        yield item
    else:
        for i in item:
            yield from extract_tests(i)


def get_suit(name: str=None, skip_names: List[str]=None) -> unittest.TestSuite:
    """Return TestSuite instance by name."""
    # Find suite:
    tl = unittest.TestLoader()
    suite = tl.loadTestsFromName(name) if name is not None else tl.discover('.', pattern='test_*.py')
    # Skip names:
    if skip_names is not None:
        for test in extract_tests(suite):
            if test.id() in skip_names:
                setattr(test, 'setUp', lambda: test.skipTest('No need to run everytime.'))
    # Return:
    return suite
