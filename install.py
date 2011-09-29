#!/usr/bin/env python

import os
import shlex
import subprocess
import sys

# Bootstrap an environment sufficient to install our application.
try:
    import setuptools
except ImportError:
    subprocess.check_call(shlex.split('easy_install setuptools --user'))

try:
    import shmac
except ImportError:
    subprocess.check_call(shlex.split('pip install git+http://github.com/mattbornski/shmac.git#egg=shmac --user'))
    os.execv(os.path.abspath(__file__), sys.argv)

try:
    import virtualenv
except ImportError:
    subprocess.check_call(shlex.split('pip virtualenv --user'))

def installed():
    return False

def install():
    print 'want to install'
    print str(dir(shmac))

def run():
    pass

if __name__ == '__main__':
    if not installed():
        install()
    run()