
import os
from setuptools import setup, find_packages

setup(
    name = 'daemoncmd', # pypi project name
    version = '0.1.0',
    license = 'MIT',
    description = ('Turn any command line into a daemon with a pidfile and ' +
                   'start, stop, restart, and status commands.'),
    long_description = open(os.path.join(os.path.dirname(__file__), 
                                         'README.md')).read(),
    keywords = ('daemon python cli init nohup commandline executable ' +
                'script pidfile'),
    scripts = ['bin/daemoncmd'],
    url = 'https://github.com/todddeluca/daemoncmd',
    author = 'Todd Francis DeLuca',
    author_email = 'todddeluca@yahoo.com',
    classifiers = ['License :: OSI Approved :: MIT License',
                   'Development Status :: 3 - Alpha',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                  ],
    py_modules = ['daemoncmd'],
)

