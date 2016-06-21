from test import support

from aiogen.utils import AsyncTestCase
from aiogen.agenerator import agenerator, async_yield
from aiogen.acontextlib import acontextmanager, AContextDecorator


class TestAContextmanager(AsyncTestCase):
    async def test_plain(self):
        state = []
        @acontextmanager
        @agenerator
        async def woohoo():
            state.append(1)
            await async_yield(42)
            state.append(999)
        async with woohoo() as x:
            self.assertEqual(state, [1])
            self.assertEqual(x, 42)

    async def test_finally(self):
        state = []
        @acontextmanager
        @agenerator
        async def woohoo():
            state.append(1)
            try:
                await async_yield(42)
            finally:
                state.append(999)
        with self.assertRaises(ZeroDivisionError):
            async with woohoo() as x:
                self.assertEqual(state, [1])
                self.assertEqual(x, 42)
                state.append(x)
                raise ZeroDivisionError()
        self.assertEqual(state, [1, 42, 999])

    async def test_no_reraise(self):
        @acontextmanager
        @agenerator
        async def whee():
            await async_yield()
        ctx = whee()
        await ctx.__aenter__()
        # Calling __exit__ should not result in an exception
        self.assertFalse(await ctx.__aexit__(TypeError, TypeError("foo"), None))

    async def test_trap_yield_after_throw(self):
        @acontextmanager
        @agenerator
        async def whoo():
            try:
                await async_yield()
            except:
                await async_yield()
        ctx = whoo()
        await ctx.__aenter__()
        with self.assertRaises(RuntimeError):
            await ctx.__aexit__(TypeError, TypeError("foo"), None)

    async def test_except(self):
        state = []
        @acontextmanager
        @agenerator
        async def woohoo():
            state.append(1)
            try:
                await async_yield(42)
            except ZeroDivisionError as e:
                state.append(e.args[0])
                self.assertEqual(state, [1, 42, 999])
        async with woohoo() as x:
            self.assertEqual(state, [1])
            self.assertEqual(x, 42)
            state.append(x)
            raise ZeroDivisionError(999)
        self.assertEqual(state, [1, 42, 999])

    async def test_except_stopiter(self):
        stop_exc = StopAsyncIteration('spam')
        @acontextmanager
        @agenerator
        async def woohoo():
            await async_yield()
        try:
            async with woohoo():
                raise stop_exc
        except Exception as ex:
            self.assertIs(ex, stop_exc)
        else:
            self.fail('StopAsyncIteration was suppressed')

    def _create_attribs(self):
        def attribs(**kw):
            def decorate(func):
                for k, v in kw.items():
                    setattr(func, k, v)
                return func
            return decorate
        @acontextmanager
        @agenerator
        @attribs(foo='bar')
        def baz(spam):
            """Whee!"""
        return baz

    async def test_attribs(self):
        baz = self._create_attribs()
        self.assertEqual(baz.__name__, 'baz')
        self.assertEqual(baz.foo, 'bar')

    @support.requires_docstrings
    async def test_doc_attrib(self):
        baz = self._create_attribs()
        self.assertEqual(baz.__doc__, "Whee!")

    @support.requires_docstrings
    async def test_instance_docstring_given_cm_docstring(self):
        baz = self._create_attribs()(None)
        self.assertEqual(baz.__doc__, "Whee!")

    async def test_keywords(self):
        @acontextmanager
        @agenerator
        async def woohoo(self, func, args, kwds):
            await async_yield((self, func, args, kwds,))
        async with woohoo(self=11, func=22, args=33, kwds=44) as target:
            self.assertEqual(target, (11, 22, 33, 44))


class mycontext(AContextDecorator):
    started = False
    exc = None
    catch = False

    async def __aenter__(self):
        self.started = True
        return self

    async def __aexit__(self, *exc):
        self.exc = exc
        return self.catch


class TestAContextDecorator(AsyncTestCase):
    @support.requires_docstrings
    async def test_instance_docs(self):
        cm_docstring = mycontext.__doc__
        obj = mycontext()
        self.assertEqual(obj.__doc__, cm_docstring)

    async def test_contextdecorator(self):
        context = mycontext()
        async with context as result:
            self.assertIs(result, context)
            self.assertTrue(context.started)
        self.assertEqual(context.exc, (None, None, None))

    async def test_contextdecorator_with_exception(self):
        context = mycontext()
        with self.assertRaisesRegex(NameError, 'foo'):
            async with context:
                raise NameError('foo')
        self.assertIsNotNone(context.exc)
        self.assertIs(context.exc[0], NameError)

        context = mycontext()
        context.catch = True
        async with context:
            raise NameError('foo')
        self.assertIsNotNone(context.exc)
        self.assertIs(context.exc[0], NameError)

    async def test_decorator(self):
        context = mycontext()
        @context
        async def test():
            self.assertIsNone(context.exc)
            self.assertTrue(context.started)
        await test()
        self.assertEqual(context.exc, (None, None, None))

    async def test_decorator_with_exception(self):
        context = mycontext()
        @context
        async def test():
            self.assertIsNone(context.exc)
            self.assertTrue(context.started)
            raise NameError('foo')
        with self.assertRaisesRegex(NameError, 'foo'):
            await test()
        self.assertIsNotNone(context.exc)
        self.assertIs(context.exc[0], NameError)

    async def test_decorating_method(self):
        context = mycontext()
        class Test(object):
            @context
            async def method(self, a, b, c=None):
                self.a = a
                self.b = b
                self.c = c
        # these tests are for argument passing when used as a decorator
        test = Test()
        await test.method(1, 2)
        self.assertEqual(test.a, 1)
        self.assertEqual(test.b, 2)
        self.assertEqual(test.c, None)

        test = Test()
        await test.method('a', 'b', 'c')
        self.assertEqual(test.a, 'a')
        self.assertEqual(test.b, 'b')
        self.assertEqual(test.c, 'c')

        test = Test()
        await test.method(a=1, b=2)
        self.assertEqual(test.a, 1)
        self.assertEqual(test.b, 2)

    async def test_typo_enter(self):
        class mycontext(AContextDecorator):
            async def __unter__(self):
                pass
            async def __aexit__(self, *exc):
                pass
        with self.assertRaises(AttributeError):
            async with mycontext():
                pass

    async def test_typo_exit(self):
        class mycontext(AContextDecorator):
            async def __enter__(self):
                pass
            async def __uxit__(self, *exc):
                pass
        with self.assertRaises(AttributeError):
            async with mycontext():
                pass

    async def test_contextdecorator_as_mixin(self):
        class somecontext:
            started = False
            exc = None
            async def __aenter__(self):
                self.started = True
                return self
            async def __aexit__(self, *exc):
                self.exc = exc
        class mycontext(somecontext, AContextDecorator):
            pass
        context = mycontext()
        @context
        async def test():
            self.assertIsNone(context.exc)
            self.assertTrue(context.started)
        await test()
        self.assertEqual(context.exc, (None, None, None))

    async def test_contextmanager_as_decorator(self):
        @acontextmanager
        @agenerator
        async def woohoo(y):
            state.append(y)
            await async_yield()
            state.append(999)

        state = []
        @woohoo(1)
        async def test(x):
            self.assertEqual(state, [1])
            state.append(x)
        await test('something')
        self.assertEqual(state, [1, 'something', 999])

        state = []
        await test('something else')
        self.assertEqual(state, [1, 'something else', 999])
