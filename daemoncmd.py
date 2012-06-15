#!/usr/bin/env python

'''
For more information on daemons in python, see:

* http://pypi.python.org/pypi/python-daemon
* http://www.python.org/dev/peps/pep-3143/
* http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
* http://en.wikipedia.org/wiki/Daemon_(computing)

Similar implementations:

* https://github.com/indexzero/forever

This module has two separate uses cases: 
    
* running a command as a daemon process
* forking the current process as a daemon.

Daemonizing a command allows one to start, stop, and restart a non-daemon
command as a daemon process.  This requires specifying a pid file which is used
to interact with the process.

Usage examples:

    python daemoncmd.py start --pidfile /tmp/daemon.pid \
            --stdout /tmp/daemon.log --stderr /tmp/daemon.log sleep 100
    python daemoncmd.py restart --pidfile /tmp/daemon.pid \
            --stdout /tmp/daemon.log --stderr /tmp/daemon.log sleep 100
    python daemoncmd.py status --pidfile /tmp/daemon.pid
    python daemoncmd.py stop --pidfile /tmp/daemon.pid

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
* If daemoncmd.py is run by monit, etc., PATH and other env vars might be
  restricted for security reasons.
* daemoncmd.py does not try to run the daemon as a particular uid.  That would
  be handled by a process manager like monit, launchd, init, god, etc.
* When running under monit, etc., pass environment variables to the command
  like so:

    FOO=testing ./daemoncmd.py start --pidfile /tmp/daemon.pid \
            --stdout /tmp/daemon.log printenv FOO
'''


import sys
import os
import signal
import errno
import argparse
import time


START = 'start'
STOP = 'stop'
RESTART = 'restart'
STATUS = 'status'


def start(argv, pidfile, stdin='/dev/null', stdout='/dev/null',
          stderr='/dev/null'):
    '''
    Start a new daemon, saving its pid to pidfile.
    Do not start the daemon if the pidfile exists and the pid in it is running.
    '''
    # use absolute path, since daemonize() changes cwd
    pidfile = os.path.abspath(pidfile)
    pid = getpid(pidfile)

    # start process pidfile does not have pid or the pid is not a running
    # process.
    if pid and running(pid):
        mess = "Start aborted since pid file '%s' exists" % pidfile
        mess += " and pid '%s' is running.\n" % pid
        sys.stderr.write(mess)
        sys.exit(1)

    sys.stdout.write('Starting process.\n')
    daemonize_command(argv, pidfile, stdin, stdout, stderr)


def stop(pidfile):
    '''
    pidfile: a file containing a process id.
    stop the pid in pidfile if pidfile contains a pid and it is running.
    '''
    # use absolute path, since daemonize() changes cwd
    pidfile = os.path.abspath(pidfile)
    pid = getpid(pidfile)

    # stop process (if it exists)
    if not pid:
        sys.stderr.write(("Warning: Could not stop process because pid file "
                          "'%s' is missing.\n" % pidfile))
    elif not running(pid):
        sys.stderr.write(('Warning: pid "%s" in pid file "%s" is already not '
                          'running.\n' % (pid, pidfile)))
    else:
        sys.stdout.write('Stopping process. pid={}\n'.format(pid))
        try:
            os.kill(pid, signal.SIGTERM)
            # a pause, so daemon will have a chance to stop before it gets restarted.
            time.sleep(1) 
        except OSError as err:
            sys.stderr.write('Failed to terminate pid "%s".  Exception: %s.\n'
                             % (pid, err))
            sys.exit(1)


def restart(argv, pidfile, stdin='/dev/null', stdout='/dev/null',
            stderr='/dev/null'):
    '''
    stop the process in pidfile.  start argv as a new daemon process.  save its
    pid to pidfile.
    '''
    stop(pidfile)
    start(argv, pidfile, stdin, stdout, stderr)


def status(pidfile):
    # use absolute path, since daemonize() changes cwd
    pidfile = os.path.abspath(pidfile)
    pid = getpid(pidfile)
    if pid and running(pid):
        sys.stdout.write('process running; pid={}\n'.format(pid))
    else:
        sys.stdout.write('process stopped\n')
        

def daemonize_command(argv, pidfile, stdin='/dev/null', stdout='/dev/null',
                      stderr='/dev/null'):
    '''
    argv: list of executable and arguments.  First item is the executable. e.g.
    ['/bin/sleep', '100']
    pidfile: filename.  pid of the daemon child process will be written to the
    file.  This is useful for monitoring services that need a pid to stop the
    daemon, etc.

    Calls daemonize, which exits the calling process and continues in the child
    process.  Therefore all code after calling daemonize_command will be
    executed in the daemon process.
    '''
    # use absolute path, since daemonize() changes cwd
    pidfile = os.path.abspath(pidfile)
    daemonize(stdin, stdout, stderr)
    # now we are in the daemon process

    # save pid to a file
    if pidfile:
        setpid(os.getpid(), pidfile)

    # do not spawn a subprocess, since the daemon process is the one we want to
    # start/stop/restart/etc.
    os.execvp(argv[0], argv)

    
def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
    '''
    stdin, stdout, stderr: filename that will be opened and used to replace the
    standard file descriptors is sys.stdin, sys.stdout, sys.stderr.  Default to
    /dev/null.  Note that stderr is opened unbuffered, so if it shares a file
    with stdout then interleaved output may not appear in the order that you
    expect.

    Turn current process into a daemon.
    returns: nothing in particular.
    '''

    # use absolute path, since daemonize() changes cwd
    stdin = os.path.abspath(stdin)
    stdout = os.path.abspath(stdout)
    stderr = os.path.abspath(stderr)
    
    # Do first fork
    try: 
        pid = os.fork() 
    except OSError as e:
        sys.stderr.write("fork #1 failed: (%d) %s\n"%(e.errno, e.strerror))
        sys.exit(1)
    if pid > 0:
        sys.exit(0) # exit parent
        
    # Decouple from parent environment.
    os.chdir("/") 
    os.umask(0) 
    os.setsid() 

    # Do second fork.
    try: 
        pid = os.fork() 
    except OSError as e: 
        sys.stderr.write("fork #2 failed: (%d) %s\n"%(e.errno, e.strerror))
        sys.exit(1)
    if pid > 0:
        sys.exit(0) # exit parent

    # Now I am a daemon!
    
    # Redirect standard file descriptors. First open the new files, perform
    # hack if necessary, flush any existing output, and dup new files to std
    # streams.
    si = open(stdin, 'r')
    so = open(stdout, 'a+')
    se = open(stderr, 'a+', 0)

    # hack and bug: when sys.stdin.close() has already been called,
    # os.dup2 throws an exception: ValueError: I/O operation on closed file
    # This hack attempts to detect whether any of the std streams
    # have been closed and if so opens them to a dummy value which
    # will get closed by os.dup2, which I like better than
    # an exception being thrown.
    if sys.stdin.closed: sys.stdin = open('/dev/null', 'r')
    if sys.stdout.closed: sys.stdout = open('/dev/null', 'a+')
    if sys.stderr.closed: sys.stderr = open('/dev/null', 'a+')
    
    sys.stdout.flush()
    sys.stderr.flush()

    os.dup2(si.fileno(), sys.stdin.fileno())
    os.dup2(so.fileno(), sys.stdout.fileno())
    os.dup2(se.fileno(), sys.stderr.fileno())


def getpid(pidfile):
    '''
    read pid from pidfile
    return: pid
    '''
    pid = None
    if os.path.isfile(pidfile):
        with open(pidfile) as fh:
            pid = int(fh.read().strip())
    return pid


def setpid(pid, pidfile):
    '''
    save pid to pidfile
    '''
    with open(pidfile, 'w') as fh:
        fh.write('{}\n'.format(pid))


def running(pid):
    """
    pid: a process id
    Return: False if the pid is None or if the pid does not match a
    currently-running process.
    Derived from code in http://pypi.python.org/pypi/python-daemon/ runner.py
    """
    if pid is None:
        return False
    try:
        os.kill(pid, signal.SIG_DFL)
    except OSError, exc:
        if exc.errno == errno.ESRCH:
            # The specified PID does not exist
            return False
    return True


def main():    
    # daemoncmd.py <command>
    # daemoncmd.py start --pidfile <file> [--stdin <file>] [--stdout <file>] \
    #   [--stderr <file>] <command>
    # daemoncmd.py restart --pidfile <file> [--stdin <file>] [--stdout <file>]\
    #   [--stderr <file>] <command>
    # daemoncmd.py stop --pidfile <file>
    # daemoncmd.py status --pidfile <file>

    parser = argparse.ArgumentParser(
        description=('Start, stop, restart or get the status of a daemon '
                     'that runs a command.'))
    subparsers = parser.add_subparsers(dest='action')

    # create the parser for the "start" command
    startParser = subparsers.add_parser('start', 
                                        help='start a daemon to run a command')
    startParser.add_argument(
        '--pidfile', required=True, 
        help='file in which to store the pid of the started daemon process')
    startParser.add_argument('--stdin', default='/dev/null', 
                             help='redirect daemon stdin from this file')
    startParser.add_argument('--stdout', default='/dev/null', 
                             help='redirect daemon stdout to this file')
    startParser.add_argument('--stderr', default='/dev/null', 
                             help='redirect daemon stderr to this file')
    startParser.add_argument(
        'cmd', 
        help=('the executable/command that the daemon will run.  i.e. a '
              'server that listens on a port for incoming connections.'))
    startParser.add_argument('args', nargs='*', 
                             help='options or arguments to the command')
    
    stopParser = subparsers.add_parser('stop', help='stop a running daemon')
    stopParser.add_argument('--pidfile', required=True, 
                            help='file containing the pid of daemon process')

    stopParser = subparsers.add_parser(
        'status', help='print the status of a daemon process')
    stopParser.add_argument('--pidfile', required=True, 
                            help='file containing the pid of daemon process')

    restartParser = subparsers.add_parser(
        'restart', help='restart a daemon to run a command')
    restartParser.add_argument(
        '--pidfile', required=True, 
        help='file in which to store the pid of the started daemon process')
    restartParser.add_argument('--stdin', default='/dev/null', 
                               help='redirect daemon stdin from this file')
    restartParser.add_argument('--stdout', default='/dev/null', 
                               help='redirect daemon stdout to this file')
    restartParser.add_argument('--stderr', default='/dev/null', 
                               help='redirect daemon stderr to this file')
    restartParser.add_argument(
        'cmd', 
        help=('the executable/command that the daemon will run.  i.e. a '
              'server that listens on a port for incoming connections.'))
    restartParser.add_argument('args', nargs='*', 
                               help='options or arguments to the command')

    args = parser.parse_args()
    
    if args.action == START:
        start([args.cmd] + args.args, args.pidfile, args.stdin, args.stdout, args.stderr)
    elif args.action == RESTART:
        restart([args.cmd] + args.args, args.pidfile, args.stdin, args.stdout, args.stderr)
    elif args.action == STOP:
        stop(args.pidfile)
    elif args.action == STATUS:
        status(args.pidfile)
        
    
if __name__ == '__main__':
    main()

