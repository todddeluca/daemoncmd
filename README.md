
## Introduction

My first introduction to running a command as a daemon looked like this:

    nohup mycommand --myoption myarg >/dev/null 2>/dev/null &

While this is a good for doing some development work, a daemon requires quite a
number of other things to happen.  The wikipedia page
http://en.wikipedia.org/wiki/Daemon\_(computing) says the following needs to
happen:

- Dissociating from the controlling tty
- Becoming a session leader
- Becoming a process group leader
- Executing as a background task by forking and exiting (once or twice). This
  is required sometimes for the process to become a session leader. It also
  allows the parent process to continue its normal execution.
- Setting the root directory ("/") as the current working directory so that the
  process does not keep any directory in use that may be on a mounted file
  system (allowing it to be unmounted).
- Changing the umask to 0 to allow open(), creat(), et al. operating system
  calls to provide their own permission masks and not to depend on the umask of
  the caller
- Closing all inherited files at the time of execution that are left open by
  the parent process, including file descriptors 0, 1 and 2 (stdin, stdout,
  stderr). Required files will be opened later.
- Using a logfile, the console, or /dev/null as stdin, stdout, and stderr

Additionally, when running a process under monit or initd, it is typical for
the process id of the daemon to be stored in a file, so the daemon can be
monitored and killed easily.

Finally, it is common to use `start`, `stop`, `restart`, and
`status` commands to control the daemon.

Daemoncmd takes care of creating a daemon the right way, putting its pid in
a file, and interacting with the daemon via `start`, `stop`, etc. commands.
Using it is as simple as:

    /path/to/daemoncmd start --pidfile /tmp/mydaemon.pid /path/to/mycommand

See the Usage section for more details.

For more information on daemons in python, see:

* http://pypi.python.org/pypi/python-daemon
* http://www.python.org/dev/peps/pep-3143/
* http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
* http://en.wikipedia.org/wiki/Daemon\_(computing)


## Alternatives

Here are some projects that are similar in scope to daemoncmd:

* http://pypi.python.org/pypi/zdaemon/2.0.4, and see
  http://ridingpython.blogspot.cz/2011/08/turning-your-python-script-into-linux.html
  for a description.
* https://github.com/indexzero/forever

While daemoncmd is a great way to start running a daemon, there are many
programs designed to run and monitor processes in a way that is more robust and
full-featured than simply starting your own daemon.  Here is a list of some of
them (see http://news.ycombinator.com/item?id=1368855 for a discussion):

- monit http://mmonit.com/monit/
- supervisord http://supervisord.org/
- daemonize http://bmc.github.com/daemonize/
- runit http://smarden.sunsite.dk/runit/
- perp http://b0llix.net/perp/
- launchd http://launchd.macosforge.org/
- daemontools http://cr.yp.to/daemontools.html

For production systems, I recommend using a tool like one of these.  I have
used supervisord and monit before.  Some of these tools work with daemons, like
monit, in which case daemoncmd could come in handy.  Other tools, like
supervisord, can supervise your process in such a way that you do not need to
daemonize it.


## Contribute

If this project does not do what you want, please open an issue or a pull
request on github, https://github.com/todddeluca/daemoncmd.


## Requirements

- Probably Python 2.7 (since that is the only version it has been tested with.)


## Installation

### Install from pypi.python.org

Download and install python-vagrant:

    pip install daemoncmd

### Install from github.com

Clone and install daemoncmd:

    git clone git@github.com:todddeluca/daemoncmd.git
    cd daemoncmd
    python setup.py install


## Usage

This module has two separate uses cases: 
    
* running a command as a daemon process
* forking the current python process as a daemon.

Daemonizing a command allows one to start, stop, and restart a non-daemon
command as a daemon process.  This requires specifying a pid file which is used
to interact with the process.

Usage examples:

     daemoncmd start --pidfile /tmp/daemon.pid \
            --stdout /tmp/daemon.log --stderr /tmp/daemon.log sleep 100
     daemoncmd restart --pidfile /tmp/daemon.pid \
            --stdout /tmp/daemon.log --stderr /tmp/daemon.log sleep 100
     daemoncmd status --pidfile /tmp/daemon.pid
     daemoncmd stop --pidfile /tmp/daemon.pid

Another use case is forking the current process into a daemon.  According
to pep 3143, forking as a daemon might be done by the standard library some
day.

Usage example:

    import daemoncmd
    import mytask

    daemoncmd.daemonize()
    mytask.doit()

Or from the command line:

    python -c 'import daemoncmd, mytask; daemoncmd.daemonize(); mytask.doit()'

Other usage notes:

* The command should not daemonize itself, since that is what this script does
  and it would make the pid in the pidfile incorrect.
* The command should be refer to the absolute path of the executable, since
  daemonization sets the cwd to '/'.  More generally, do not assume what the
  cwd is.
* If daemoncmd is run by monit, etc., PATH and other env vars might be
  restricted for security reasons.
* daemoncmd does not try to run the daemon as a particular uid.  That would
  be handled by a process manager like monit, launchd, init, god, etc.
* When running under monit, etc., pass environment variables to the command
  like so:

    FOO=testing daemoncmd start --pidfile /tmp/daemon.pid \
            --stdout /tmp/daemon.log printenv FOO





