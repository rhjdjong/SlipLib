# Copyright (c) 2017 Ruud de Jong
# This file is part of the SlipLib project which is released under the MIT license.
# See https://github.com/rhjdjong/SlipLib for details.

from setuptools import setup, find_packages  # Always prefer setuptools over distutils
# noinspection PyPep8Naming
from setuptools.command.test import test as TestCommand
import os.path
import sys


version_dict = {}
with open(os.path.join('src', 'sliplib', 'version.py')) as version_file:
    exec(version_file.read(), version_dict)
__version__ = version_dict['__version__']
del version_dict


# Get the long description from the relevant file
def read_long_description(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    seperator = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return seperator.join(buf)


class PyTest(TestCommand):
    user_options = [('pytest-args=', 'a', 'Arguments to pass to py.test')]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run(self):
        # import here, cause outside the eggs aren't loaded
        import pytest
        errno = pytest.main(self.pytest_args)  # @UndefinedVariable
        sys.exit(errno)


long_description = read_long_description('README.rst')


setup(
    name='sliplib',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version=__version__,
    #version=sliplib.__version__,

    description='Slip package',
    long_description=long_description,

    # The project's main homepage.
    url='https://github.com/rhjdjong/SlipLib',

    # Author details
    author='Ruud de Jong',
    author_email='ruud.de.jong@xs4all.nl',

    # Choose your license
    license='MIT',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: MIT License',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        #         'Programming Language :: Python :: 2',
        #         'Programming Language :: Python :: 2.6',
        #         'Programming Language :: Python :: 2.7',
        #         'Programming Language :: Python :: 3',
        #         'Programming Language :: Python :: 3.2',
        #         'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],

    # What does your project relate to?
    keywords='slip message framing protocol RFC1055',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    package_dir={'': 'src'},
    packages=find_packages('src'),

    tests_require=['pytest>=3.0', 'pytest-mock'],
    cmdclass={'test': PyTest},
    extras_require={
        'dev': ['sphinx_rtd_theme'],
        'test': ['pytest', 'coverage', 'pytest-cov']
    }
)
