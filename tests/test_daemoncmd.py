



import subprocess
import os
import sys


PID_FILE = os.path.abspath('test_daemon.pid')
LOG_FILE = os.path.abspath('test_daemon.log')

# assume this directory structure
# project/tests/test_daemoncmd.py
# project/daemoncmd.py

HERE = os.path.dirname(os.path.abspath(__file__))
DC_PATH = os.path.join(os.path.dirname(HERE), 'daemoncmd.py')
DAEMONCMD = sys.executable + ' ' + DC_PATH

def test_cli():
    '''
    Test start, status, restart, and stop using the bin/daemoncmd command
    line interface.  The "test" is that the subprocess calls do not return a
    non-zero return code.
    '''
    kws = {'pid': PID_FILE, 'out': LOG_FILE, 'err': LOG_FILE}

    status_cmd = DAEMONCMD + ' status --pidfile {pid}'
    status_cmd = status_cmd.format(**kws)
    stop_cmd = DAEMONCMD + ' stop --pidfile {pid}'
    stop_cmd = stop_cmd.format(**kws)
    start_cmd = DAEMONCMD + ' start --pidfile {pid} --stdout {out}'
    start_cmd += ' --stderr {err} sleep 10'
    start_cmd = start_cmd.format(**kws)
    restart_cmd = DAEMONCMD + ' restart --pidfile {pid} --stdout {out}'
    restart_cmd += ' --stderr {err} sleep 10'
    restart_cmd = restart_cmd.format(**kws)
    try:
        # check the process is not running yet.
        output = subprocess.check_output(status_cmd, shell=True)
        print output.find('stopped')
        assert output.find('stopped') != -1

        # start process
        cmd = DAEMONCMD + ' start --pidfile {pid} --stdout {out}'
        cmd += ' --stderr {err} sleep 10'
        output = subprocess.check_output(start_cmd, shell=True)

        # check that process is running
        cmd = DAEMONCMD + ' status --pidfile {pid}'
        output = subprocess.check_output(status_cmd, shell=True)
        print output.find('running')
        assert output.find('running') != -1

        # restart process
        cmd = DAEMONCMD + ' restart --pidfile {pid} --stdout {out}'
        cmd += ' --stderr {err} sleep 10'
        output = subprocess.check_output(restart_cmd, shell=True)

        # check that process is running
        cmd = DAEMONCMD + ' status --pidfile {pid}'
        output = subprocess.check_output(status_cmd, shell=True)
        print output.find('running')
        assert output.find('running') != -1

        # stop process
        cmd = 'bin/daemoncmd stop --pidfile {pid}'
        output = subprocess.check_output(stop_cmd, shell=True)

        # check that process is stopped
        cmd = 'bin/daemoncmd status --pidfile {pid}'
        output = subprocess.check_output(status_cmd, shell=True)
        print output.find('stopped')
        assert output.find('stopped') != -1
    finally:
        for path in (PID_FILE, LOG_FILE):
            if os.path.exists(path):
                os.remove(path)



