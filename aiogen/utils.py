from typing import List, Iterable
import asyncio as aio
import unittest
from functools import wraps


# TASKS:
def add_async_callback(fut: aio.Future, coro):
    print('!', fut)  # TODO !!!
    done = aio.Future()
    # Delegate all "fut"'s callbacks to "done" event:
    for cb in fut._callbacks:
        fut.remove_done_callback(cb)
        done.add_done_callback(cb)
    # Start task to set "done" on "fut" done:
    async def async_callback():
        try:
            await coro
        except Exception as exc:
            loop = aio.get_event_loop()
            context = {
                'message': 'Exception in async callback {}'.format(coro),
                'exception': exc,
            }
            loop.call_exception_handler(context)
        finally:
            print('!!', fut)  # TODO !!!
            try:
                done.set_result(None)
            except Exception as exc:
                print('!!!', type(exc), exc)  # TODO !!!
    fut.add_done_callback(lambda t: aio.ensure_future(async_callback()))

# TESTS:
class AsyncTestCase(unittest.TestCase):
    """TestCase to run all coroutine functions in class in separate event loop."""
    @classmethod
    def setUpClass(cls):
        names = unittest.TestLoader().getTestCaseNames(cls)
        for name, obj in vars(cls).items():
            if (name in names) and aio.iscoroutinefunction(obj):
                setattr(cls, name, _run_in_loop(obj))


def _run_in_loop(func_to_decorate):
    """Decorator to run coroutine in event loop."""
    @wraps(func_to_decorate)
    def wrapper(*args, **kwargs):
        loop = aio.new_event_loop()
        aio.set_event_loop(loop)
        loop.set_debug(True)
        try:
            loop.run_until_complete(func_to_decorate(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


# HELPERS:
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

