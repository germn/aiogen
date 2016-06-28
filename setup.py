from distutils.core import setup
import sys


if sys.version_info < (3, 5, 2):
    raise RuntimeError("aiogen requires Python 3.5.2+")

setup(
    name='aiogen',
    packages=['aiogen'],
    version='0.11',
    description='Asynchronous generators for asyncio',
    long_description='`Package Documentation <https://github.com/germn/aiogen/blob/master/README.md>`',
    author='Gerasimov Mikhail',
    author_email='Gerasimov-M-N@yandex.ru',
    url='https://github.com/germn/aiogen',
    download_url='https://github.com/germn/aiogen/tarball/master',
    license='MIT',
    keywords=[
        'asyncio',
        'asynchronous generator'
    ],
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
    ],
)
