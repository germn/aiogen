from typing import Union, List, Tuple, Dict, Set, FrozenSet, Callable
from collections.abc import Iterable, Iterator, AsyncIterable, AsyncIterator
from collections import deque

from aiogen.agenerator import agenerator, async_yield


__all__ = (
    'aall', 'aany', 'adict', 'aenumerate', 'afilter',
    'afrozenset', 'aiter', 'alist', 'amap', 'amax', 'amin',
    'anext', 'aset', 'asorted', 'asum', 'atuple', 'azip',
)


async def aall(aiterable: AsyncIterable) -> bool:
    async for element in aiterable:
        if not element:
            return False
    return True


async def aany(aiterable: AsyncIterable) -> bool:
    async for element in aiterable:
        if element:
            return True
    return False


async def adict(aiterable: AsyncIterable) -> Dict:
    return dict(await alist(aiterable))


@agenerator
async def aenumerate(aiterable: AsyncIterable, start: int=0) -> AsyncIterator:
    n = start
    async for element in aiterable:
        await async_yield((n, element,))
        n += 1


@agenerator
async def afilter(function: Callable, aiterable: AsyncIterable) -> AsyncIterator:
    function = function if function is not None else bool
    async for element in aiterable:
        if function(element):
            await async_yield(element)


async def afrozenset(aiterable: AsyncIterable) -> FrozenSet:
    return frozenset(await alist(aiterable))


def aiter(*args):
    """Note: aiter expect first arg coroutine function if two arguments passed."""
    if len(args) == 1:
        aiterable, *_ = args
        return aiterable.__aiter__()
    elif len(args) == 2:
        coro_func, sentinel, *_ = args
        @agenerator
        async def iterator():
            while True:
                res = await coro_func()
                if res != sentinel:
                    await async_yield(res)
                else:
                    break
        return iterator()
    else:
        raise TypeError(
            '{fname} expected at most {most} arguments, got {got}'
            .format(fname=aiter.__name__, most=2, got=len(args))
        )


async def alist(aiterable: AsyncIterable) -> List:
    d = deque()
    d_append = d.append
    async for element in aiterable:
        d_append(element)
    return list(d)


@agenerator
async def amap(function: Callable, *iterables: List[Union[Iterable, AsyncIterable]]) -> AsyncIterator:
    """Note: amap supports both iterables and aiterables."""
    async for args in azip(*iterables):
        await async_yield(function(*args))


async def amax(*args, **kwargs):
    if len(args) == 1:
        args = (await alist(args[0]), )
    return max(*args, **kwargs)


async def amin(*args, **kwargs):
    if len(args) == 1:
        args = (await alist(args[0]), )
    return min(*args, **kwargs)


async def anext(*args):
    if len(args) == 1:
        aiterator, *_ = args
        try:
            return await aiterator.__anext__()
        except StopAsyncIteration as exc:
            raise exc
    if len(args) == 2:
        aiterator, default, *_ = args
        try:
            return await aiterator.__anext__()
        except StopAsyncIteration as exc:
            return default
    else:
        raise TypeError(
            '{fname} expected at most {most} arguments, got {got}'
            .format(fname=anext.__name__, most=2, got=len(args))
        )


async def aset(aiterable: AsyncIterable) -> Set:
    return set(await alist(aiterable))


async def asorted(aiterable: AsyncIterable, **kwargs) -> List:
    return sorted(await alist(aiterable), **kwargs)


async def asum(aiterable: AsyncIterable, *args):
    return sum(await alist(aiterable), *args)


async def atuple(aiterable: AsyncIterable) -> Tuple:
    return tuple(await alist(aiterable))


@agenerator
async def azip(*iterables: List[Union[Iterable, AsyncIterable]]) -> AsyncIterator:
    """Note: azip supports both iterables and aiterables."""
    d = deque()
    d_append = d.append
    for it in iterables:
        d.append(
            iter(it) if isinstance(it, Iterable)
            else await aiter(it)
        )
    iterators = list(d)
    sentinel = object()
    while iterators:
        result = []
        for it in iterators:
            elem = \
                next(it, sentinel) if isinstance(it, Iterator) \
                else await anext(it, sentinel)
            if elem is sentinel:
                return
            result.append(elem)
        await async_yield(tuple(result))
