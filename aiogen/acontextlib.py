import sys
from functools import wraps


class AContextDecorator:
    def _recreate_cm(self):
        return self

    def __call__(self, coro_func):
        @wraps(coro_func)
        async def inner(*args, **kwargs):
            async with self._recreate_cm():
                return await coro_func(*args, **kwargs)
        return inner


def acontextmanager(coro_func):
    @wraps(coro_func)
    def wrapper(*args, **kwargs):
        class AGeneratorContextManager(AContextDecorator):
            def __init__(self, coro_func, args, kwargs):
                self.gen = coro_func(*args, **kwargs)
                self.coro_func, self.args, self.kwargs = coro_func, args, kwargs
                # Issue 19330:
                doc = getattr(coro_func, "__doc__", None)
                if doc is None:
                    doc = type(self).__doc__
                self.__doc__ = doc

            def _recreate_cm(self):
                return self.__class__(self.coro_func, self.args, self.kwargs)

            async def __aenter__(self):
                try:
                    return await self.gen.__anext__()
                except StopAsyncIteration:
                    raise RuntimeError("async generator didn't yield") from None

            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    try:
                        await self.gen.__anext__()
                    except StopAsyncIteration:
                        return
                    else:
                        raise RuntimeError("async generator didn't stop")
                else:
                    if exc_val is None:
                        exc_val = exc_type()
                    try:
                        await self.gen.athrow(exc_type, exc_val, exc_tb)
                        raise RuntimeError("async generator didn't stop after athrow()")
                    except StopAsyncIteration as exc:
                        return exc is not exc_val
                    except RuntimeError as exc:
                        if exc.__cause__ is exc_val:
                            return False
                        raise exc
                    except Exception as exc:
                        if sys.exc_info()[1] is not exc_val:
                            raise exc
        return AGeneratorContextManager(coro_func, args, kwargs)
    return wrapper
