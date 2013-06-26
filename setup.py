
import os
from setuptools import setup

def version(modfile):
    '''
    Parse version from module without importing or evaluating the code.
    The module should define a __version__ variable like __version__ = '2.0.1'.
    '''
    import re
    with open(modfile) as fh:
        for line in fh:
            m = re.search(r"^__version__ = '([^']+)'$", line)
            if m:
                return m.group(1)
    raise Exception('No __version__ string found in {fn}'.format(fn=modfile))

setup(
    name = 'daemoncmd', # pypi project name
    version = version('daemoncmd.py'),
    license = 'MIT',
    description = ('Turn any command line into a daemon with a pidfile and ' +
                   'start, stop, restart, and status commands.'),
    long_description = open(os.path.join(os.path.dirname(__file__), 
                                         'README.md')).read(),
    keywords = ('daemon python cli init nohup commandline executable ' +
                'script pidfile'),
    entry_points={'console_scripts': ['daemoncmd = daemoncmd:main']},
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

