from typing import AsyncIterator
from aiogen.utils import AsyncTestCase
from aiogen.agenerator import agenerator, async_yield
from aiogen.abuiltins import *


@agenerator
async def ag(iterable) -> AsyncIterator:
    for i in iterable:
        await async_yield(i)


class TestABuiltins(AsyncTestCase):
    async def test_all(self):
        # All true:
        i = [True, True, True]
        self.assertEqual(await aall(ag(i)), all(i))
        # Single false:
        i = [True, False, True]
        self.assertEqual(await aall(ag(i)), all(i))

    async def test_any(self):
        # All true:
        i = [True, True, True]
        self.assertEqual(await aany(ag(i)), any(i))
        # Single false:
        i = [True, False, True]
        self.assertEqual(await aany(ag(i)), any(i))
        # All false:
        i = [False, False, False]
        self.assertEqual(await aany(ag(i)), any(i))

    async def test_adict(self):
        i = [(1, 2), (3, 4)]
        self.assertEqual(await adict(ag(i)), dict(i))

    async def test_aenumerate(self):
        i = [1, 2, False]
        self.assertEqual(await alist(aenumerate(ag(i))), list(enumerate(i)))

    async def test_afilter(self):
        i = [7, 1, 4, 3, 2]
        f = lambda v: v > 3
        self.assertEqual(await alist(afilter(f, ag(i))), list(filter(f, i)))

    async def test_afrozenset(self):
        i = [7, 7, 0, 9, 2, 0, 7]
        self.assertEqual(await afrozenset(ag(i)), frozenset(i))

    async def test_aiter(self):
        i = [0, 1, 3, 4, 5]
        # f:
        it = iter(i)
        f = lambda: next(it)
        # af:
        ait = aiter(ag(i))
        af = lambda: anext(ait)  # coroutine
        # check:
        self.assertEqual(await alist(aiter(af, 3)), list(iter(f, 3)))

    async def test_alist(self):
        i = (0, True, 1, False, 2,)
        self.assertEqual(await alist(ag(i)), list(i))

    async def test_amap(self):
        i1 = [7, 1, 4, 3, 2]
        i2 = range(4)
        f = lambda v1, v2: v1 * v2
        self.assertEqual(await alist(amap(f, ag(i1), i2)), list(map(f, i1, i2)))

    async def test_amax(self):
        i = [7, 3, 0, 9, 2, 0, 9]
        self.assertEqual(await amax(ag(i)), max(i))

    async def test_amin(self):
        i = [7, 3, 0, 9, 2, 0, 9]
        self.assertEqual(await amin(ag(i)), min(i))

    async def test_anext(self):
        i = [1, 2]
        it = iter(i)
        ait = aiter(ag(i))
        self.assertEqual(await anext(ait), next(it))
        self.assertEqual(await anext(ait), next(it))
        self.assertEqual(await anext(ait, 3), next(it, 3))

    async def test_aset(self):
        i = [7, 7, 0, 9, 2, 0, 7]
        self.assertEqual(await aset(ag(i)), set(i))

    async def test_asorted(self):
        i = [7, 7, 0, 9, 2, 0, 7]
        self.assertEqual(await asorted(ag(i)), sorted(i))

    async def test_asum(self):
        i = [7, 7, 0, 9, 2, 0, 7]
        self.assertEqual(await asum(ag(i)), sum(i))

    async def test_atuple(self):
        i = [7, 7, 0, 9, 2, 0, 7]
        self.assertEqual(await atuple(ag(i)), tuple(i))

    async def test_azip(self):
        i1 = [7, 1, 4, 3, 2]
        i2 = range(4)
        self.assertEqual(await alist(azip(ag(i1), i2)), list(zip(i1, i2)))
