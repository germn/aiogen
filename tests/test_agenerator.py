from aiogen.utils import AsyncTestCase
from aiogen.agenerator import agenerator, async_yield, async_yield_from
from aiogen.abuiltins import anext


@agenerator
async def ay(start):
    r1 = await async_yield(start)
    r2 = await async_yield(r1)
    return r2


@agenerator
async def ayf(start):
    r1 = await async_yield_from(ay(start))
    r2 = await async_yield_from(ay(r1))
    return r2


class TestLoop(AsyncTestCase):
    async def test_loop(self):
        i = 0
        async for val in ay(1):
            if i == 0: self.assertEqual(val, 1)
            if i == 1: self.assertEqual(val, None)
            i += 1

    async def test_break(self):
        i = 0
        async for val in ay(1):
            if i == 0: self.assertEqual(val, 1)
            if i > 0: break
            i += 1

    async def test_loop_ayf(self):
        i = 0
        async for val in ayf(1):
            if i == 0: self.assertEqual(val, 1)
            if i == 1: self.assertEqual(val, None)
            if i == 2: self.assertEqual(val, None)
            if i == 3: self.assertEqual(val, None)
            i += 1

    async def test_break_ayf(self):
        i = 0
        async for val in ayf(1):
            if i == 0: self.assertEqual(val, 1)
            if i == 1: self.assertEqual(val, None)
            if i == 2: self.assertEqual(val, None)
            if i > 2: break
            i += 1


class TestASend(AsyncTestCase):
    async def test_asend(self):
        gen = ay(1)
        self.assertEqual(await anext(gen), 1)
        self.assertEqual(await gen.asend(2), 2)
        with self.assertRaises(StopAsyncIteration) as cm:
            await gen.asend(3)
        self.assertEqual(cm.exception.args[0], 3)

    async def test_asend_ayf(self):
        gen = ayf(1)
        self.assertEqual(await anext(gen), 1)
        self.assertEqual(await gen.asend(2), 2)
        self.assertEqual(await gen.asend(3), 3)
        self.assertEqual(await gen.asend(4), 4)
        with self.assertRaises(StopAsyncIteration) as cm:
            await gen.asend(5)
        self.assertEqual(cm.exception.args[0], 5)


class TestAThrow(AsyncTestCase):
    async def test_athrow_first(self):
        gen = ay(1)
        with self.assertRaises(ValueError) as cm:
            await gen.athrow(ValueError())

    async def test_athrow_after_anext(self):
        gen = ay(1)
        await anext(gen)
        with self.assertRaises(ValueError) as cm:
            await gen.athrow(ValueError())

    async def test_anext_after_athrow(self):
        gen = ay(1)
        with self.assertRaises(ValueError) as cm:
            await gen.athrow(ValueError())
        with self.assertRaises(StopAsyncIteration) as cm:
            await anext(gen)

    async def test_athrow_after_athrow(self):
        gen = ay(1)
        with self.assertRaises(ValueError) as cm:
            await gen.athrow(ValueError())
        with self.assertRaises(TypeError) as cm:
            await gen.athrow(TypeError())


class TestAClose(AsyncTestCase):
    async def test_aclose_first(self):
        gen = ay(1)
        await gen.aclose()
        with self.assertRaises(StopAsyncIteration) as cm:
            await anext(gen)

    async def test_aclose_after_anext(self):
        gen = ay(1)
        await anext(gen)
        await gen.aclose()
        with self.assertRaises(StopAsyncIteration) as cm:
            await anext(gen)

    async def test_anext_after_aclose(self):
        gen = ay(1)
        await gen.aclose()
        with self.assertRaises(StopAsyncIteration) as cm:
            await anext(gen)
        with self.assertRaises(StopAsyncIteration) as cm:
            await anext(gen)

    async def test_athrow_after_aclose(self):
        gen = ay(1)
        await gen.aclose()
        with self.assertRaises(StopAsyncIteration) as cm:
            await anext(gen)
        with self.assertRaises(ValueError) as cm:
            await gen.athrow(ValueError())
