## aiogen - asynchronous generators for asyncio

`aiogen` - is emulation of asynchronous generators for `asyncio`. While it's not full implementation, it can be used to play with asynchronous generators until this future is not implemented in Python.

Module tries to meet regular generator's behaviour as much as possible (considering it's based on coroutines).

Python 3.5.2+ required.

Note, that module isn't tested much and not recommended to use in production!

### How to create asynchronous generator

Asynchronous generator can be created by decorating coroutine with `agenerator`. Coroutines `async_yield` and `async_yield_from` uses to emulate plain generator's `yield` and `yield from`:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from


@agenerator
async def g():
    await async_yield(1)
    await async_yield(2)
    await async_yield(3)

async def main():
    async for val in g():
        print(val)

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
1
2
3
```

### Asynchronous generator's methods

Generator has method `__aiter__` and coroutines `__anext__`, `asend`, `athrow`, `aclose` similar to plain generator's methods:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from


@agenerator
async def g():
    print('inside gen', '-', await async_yield(1))
    try:
        await async_yield(2)
    except Exception as exc:
        print('inside gen', '-', repr(exc))
        raise exc

async def main():
    gen = g()
    print('from gen', '-', await gen.__anext__())
    print('from gen', '-', await gen.asend(123))
    try:
        await gen.athrow(ValueError())
    except Exception as exc:
        print('from gen', '-', repr(exc))
        # raise exc

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
from gen - 1
inside gen - 123
from gen - 2
inside gen - ValueError()
from gen - ValueError()
```

### StopAsyncIteration and AsyncGeneratorExit

If there's no more values to `async_yield` generator's `asend` raises `StopAsyncIteration`:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from


@agenerator
async def g():
    await async_yield(1)

async def main():
    gen = g()
    await gen.__anext__()
    await gen.__anext__()  # raises StopAsyncIteration

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

`AsyncGeneratorExit` raises inside async generator on `aclose`. Note, that `AsyncGeneratorExit` inherited from `Exception` (unlike `GeneratorExit` inherited from `BaseException`).

`aclose` would be called for unclosed async generator on outer task done, but before event loop closed:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from


@agenerator
async def g():
    try:
        await async_yield(1)
    except Exception as exc:
        print(repr(exc))  # AsyncGeneratorExit()
        raise exc

async def main():
    gen = g()
    await gen.__anext__()

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

As in plain generator you'll get `RuntimeError` if you ignored `AsyncGeneratorExit` and try to `async_yield` some value:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from


@agenerator
async def g():
    try:
        await async_yield(1)
    except Exception as exc:
        await async_yield(2)  # RuntimeError('generator ignored AsyncGeneratorExit')

async def main():
    gen = g()
    await gen.__anext__()

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

## abuiltins

Python has builtin function that works with `Iterable` arguments. `aiogen.abuiltins` has similar functions to work with `AsyncIterable` args:

`aall`, `aany`, `adict`, `aenumerate`, `afilter`, `afrozenset`, `aiter`, `alist`, `amap`, `amax`, `amin`, `anext`, `aset`, `asorted`, `asum`, `atuple`, `azip`

This methods act like originals considering being designed for `AsyncIterable` args.

`aall`, `aany`, `adict`, `afrozenset`, `alist`, `amax`, `amin`, `anext`, `aset`, `asorted`, `asum`, `atuple` are coroutines:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from
from aiogen.abuiltins import aall, aany


@agenerator
async def g():
    await async_yield(True)
    await async_yield(False)
    await async_yield(True)

async def main():
    print(await aall(g()))
    print(await aany(g()))

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
False
True
```

`aenumerate`, `afilter`, `aiter`, `amap`, `azip` are async iterators:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from
from aiogen.abuiltins import aenumerate


@agenerator
async def g():
    await async_yield('a')
    await async_yield('b')
    await async_yield('c')

async def main():
    async for i, val in aenumerate(g()):
        print(i, val)

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
0 a
1 b
2 c
```

`amap`, `azip` can accept both `AsyncIterable` and `Iterable` args:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from
from aiogen.abuiltins import azip


@agenerator
async def g():
    await async_yield('a')
    await async_yield('b')
    await async_yield('c')

async def main():
    async for val in azip(g(), range(5)):
        print(val)

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
('a', 0)
('b', 1)
('c', 2)
```

In case `aiter` has two args, first one expected to be coroutine function:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from
from aiogen.abuiltins import aiter


it = iter(['a', 'b', 'c', 'sentinel'])

async def coro_func():
    return next(it)

async def main():
    async for val in aiter(coro_func, 'sentinel'):
        print(val)

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
a
b
c
```

## acontextlib

`aiogen.acontextlib` is `contextlib` for async generators:

```python
import asyncio as aio

from aiogen.agenerator import agenerator, async_yield, async_yield_from
from aiogen.acontextlib import acontextmanager


@acontextmanager
@agenerator
async def acm():
    print('before')
    await async_yield('middle')
    print('after')

async def main():
    async with acm() as val:
        print(val)

if __name__ == "__main__":
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
```

Outputs:

```
before
middle
after
```