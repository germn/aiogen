import sys
import asyncio as aio
from functools import wraps

from aiogen.utils import add_async_callback


class AsyncGeneratorExit(Exception):
    pass


def agenerator(coro_func):
    @wraps(coro_func)
    def wrapper(*args, **kwargs):
        class AsyncGenerator:
            def __init__(self):
                self._loop = aio.get_event_loop()
                self._task = None
                self._incoming = aio.Future()  # incoming = async_yield()
                self._outcoming = aio.Future()  # async_yield(outcoming)

            @aiter_compat
            def __aiter__(self):
                return self

            async def __anext__(self):
                return await self.asend(None)

            async def asend(self, incoming):
                # First incoming value is not None:
                if self._task is None and incoming is not None:
                    raise TypeError('can\'t send non-None value to a just-started generator')
                # First incoming value, start generator:
                elif self._task is None:
                    self._task = aio.ensure_future(coro_func(*args, **kwargs))
                    self._task._gen = self
                    # Generator exit on outer task done:
                    async def gen_exit():
                        try:
                            await self.aclose()
                        # If close ignored, we will see it,
                        # no need to keep pending task:
                        finally:
                            if not self._task.done():
                                self._task.set_result(None)
                    outer = aio.Task.current_task()
                    add_async_callback(outer, gen_exit())
                # Gen closed, raise StopAsyncIteration:
                elif self._task.done():
                    raise StopAsyncIteration()
                # Set incoming value:
                else:
                    self._incoming.set_result(incoming)
                # Wait for next step:
                return await self._next_step()

            async def athrow(self, exc_type, exc_val=None, exc_tb=None):
                if exc_val is None and exc_tb is None:
                    exc = exc_type
                elif exc_val is None:
                    exc = exc_type()
                else:
                    exc = exc_val
                if exc_tb is not None:
                    exc = exc.with_traceback(exc_tb)
                # First incoming exception, create gen with exception:
                if self._task is None:
                    self._task = aio.Future()
                    self._task.set_exception(exc)
                # Gen closed, just raise:
                elif self._task.done():
                    raise exc
                # Set incoming exception:
                else:
                    self._incoming.set_exception(exc)
                # Wait for next step:
                return await self._next_step()

            async def aclose(self):
                try:
                    await self.athrow(AsyncGeneratorExit())
                except (AsyncGeneratorExit, StopAsyncIteration):
                    pass
                else:
                    raise RuntimeError("generator ignored AsyncGeneratorExit")

            async def _next_step(self):
                # Wait for next outcoming value (async_yield) or task complete:
                await aio.wait([self._outcoming, self._task], return_when=aio.FIRST_COMPLETED)
                # async_yield happened:
                if self._outcoming.done():
                    try:
                        return self._outcoming.result()
                    finally:
                        self._outcoming = aio.Future()
                # Generator was cancelled:
                elif self._task.cancelled():
                    raise aio.CancelledError()
                # Generator finished with AsyncGeneratorExit:
                elif isinstance(self._task.exception(), AsyncGeneratorExit):
                    raise StopAsyncIteration()
                # Generator finished with exception:
                elif self._task.exception():
                    raise self._task.exception()
                # Generator finished successfully:
                else:
                    raise StopAsyncIteration(self._task.result())
        return AsyncGenerator()
    return wrapper


async def async_yield(outcoming=None):
    # Get generator:
    task = aio.Task.current_task()
    if not hasattr(task, '_gen'):
        raise RuntimeError('async_yield outside agenerator')
    self = task._gen
    # Set outcoming value:
    self._outcoming.set_result(outcoming)
    # Wait for next incoming value:
    try:
        return await self._incoming
    finally:
        self._incoming = aio.Future()


async def async_yield_from(gen):
    # Get generator:
    task = aio.Task.current_task()
    if not hasattr(task, '_gen'):
        raise RuntimeError('async_yield_from outside agenerator')
    self = task._gen
    # Pass values from generator to current generator:
    try:
        incoming = None
        while True:
            outcoming = await gen.asend(incoming)
            # Set outcoming value:
            self._outcoming.set_result(outcoming)
            # Wait for next incoming value:
            try:
                incoming = await self._incoming
            finally:
                self._incoming = aio.Future()
    except StopAsyncIteration as exc:
        return exc.args[0]


if sys.version_info < (3, 5, 2):
    def aiter_compat(func):
        @wraps(func)
        async def wrapper(self):
            return func(self)
        return wrapper
else:
    def aiter_compat(func):
        return func
