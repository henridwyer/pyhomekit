"""Setup script for pyHomeKit.

https://github.com/henridwyer/pyhomekit
"""

from os import path
from codecs import open
from setuptools import setup, find_packages

PACKAGE = "pyhomekit"
VERSION = "0.0.1"

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=PACKAGE,
    version=VERSION,
    description='Python interface to control HomeKit accessories.',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/pypa/sampleproject',

    # Author details
    author='Henri Dwyer',
    author_email='gardianz@gmail.com',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Home Automation',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='homekit bluetooth home',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=['bluepy', 'tenacity'],
    extras_require={'dev': ['py.test', 'mypy']}, )
