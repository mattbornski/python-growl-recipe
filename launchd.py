#!/usr/bin/env python

# Only import default Python packages here.  You can't depend on any other packages being present at this point in the script execution.
from __future__ import with_statement
import os
import os.path
import shlex
import shutil
import subprocess
import sys

VENDOR = 'Bornski'
PROGRAM = 'Growl Demo'

def bootstrap(packages={}):
    # Bootstrap an environment sufficient to install our application.
    
    # The default package manager which comes with most Python installations, easy_install, is not capable of many
    # things I regularly depend on, like one-line installs from source repos.  Get pip instead.
    try:
        import setuptools
    except ImportError:
        subprocess.check_call(shlex.split('easy_install setuptools --user'))

    # Install packages you requested.  We probably don't have sudo privileges so we'll do this into user-writable
    # locations.  I do not advise installing packages your program will depend on _at run time_ into user locations,
    # since their continued existence is not at all guaranteeed.  Instead, use this to get you to the point where
    # you can install your program and its packages into a virtualenv in a permanent location, which is much more
    # likely to exist in a predictable state next time your program tries to run.
    package_refresh_required = False
    for (package_name, package_location) in packages.iteritems():
        try:
            __import__(package_name)
        except ImportError:
            subprocess.check_call(shlex.split('pip install {package_location} --user'.format(package_location=package_location)))
            package_refresh_required = True
    if package_refresh_required:
        os.execv(os.path.abspath(sys.argv[0]), sys.argv)

def installed(settings={}):
    # Check that the application folder exists and that the launchd settingsuration is valid.
    return (subprocess.call(shlex.split('launchctl list {namespace}.{program}'.format(**settings))) == 0)

def uninstall(settings={}):
    bootstrap({'shmac':'git+http://github.com/mattbornski/shmac.git#egg=shmac'})
    import shmac
    
    # Remove settings from launchd and remove the application folder.
    try:
        subprocess.call(shlex.split('launchctl unload {plist_filename}'.format(**settings)))
    except OSError:
        pass
    shmac.sudo('rm {plist_filename}'.format(**settings))#, icon=settings['icon'], name=' '.join([settings['vendor'], settings['program']]))
    try:
        shutil.rmtree(settings['application_folder'])
    except OSError:
        pass

def install(packages={}, settings={}):
    bootstrap({'shmac':'git+http://github.com/mattbornski/shmac.git#egg=shmac'})
    import shmac
    
    # Create the environment necessary to run our application
    cwd = os.getcwd()
    try:
        shutil.copytree(settings['run_folder'], settings['application_folder'], ignore=lambda src, names: [n for n in names if n in ['.git', '.gitignore']])
        os.chdir(settings['application_folder'])
        if len(packages) > 0:
            try:
                import virtualenv
            except ImportError:
                subprocess.check_call(shlex.split('pip install virtualenv --user'))
            subprocess.check_call(shlex.split('virtualenv --no-site-packages env'))
            subprocess.check_call(shlex.split('pip install ' + ' '.join(packages.values()) + ' -E env'))
            
        # Make a bash script for launchd to invoke.
        bash_filename = settings['program'] + '.sh'
        with open(bash_filename, 'w') as bash:
            bash.write('''#!/bin/bash
{virtualenv}
echo "import {program} ; {program}.run()" | /usr/bin/env python -
'''.format(virtualenv='source env/bin/activate\n' if len(packages) > 0 else '', **settings))
        os.chmod(bash_filename, 0755)
        
        # Create the launchd file for our application
        temp_plist_filename = os.path.basename(settings['plist_filename'])
        with open(temp_plist_filename, 'w') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>{namespace}.{program}</string>
    <key>Program</key>
    <string>{application_folder}/{bash_filename}</string>
    <key>WorkingDirectory</key>
    <string>{application_folder}</string>
    <key>ProgramArguments</key>
    <array>
      <string>{bash_filename}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{application_folder}/{program}.log</string>
    <key>StandardErrorPath</key>
    <string>{application_folder}/{program}.log</string>
  </dict>
</plist>'''.format(bash_filename=bash_filename, **settings))
        shmac.sudo('cp {temp_plist_filename} {plist_filename}'.format(temp_plist_filename=temp_plist_filename, **settings))#, icon=settings['icon'], name=' '.join([settings['vendor'], settings['program']]))
        os.remove(temp_plist_filename)
    finally:
        os.chdir(cwd)

def run(settings):
    # Ask launchd to start the program.
    subprocess.check_call(shlex.split('launchctl load {plist_filename}'.format(**settings)))
    subprocess.check_call(shlex.split('launchctl start {namespace}.{program}'.format(**settings)))

def restart(settings):
    subprocess.check_call(shlex.split('launchctl stop {namespace}.{program}'.format(**settings)))
    subprocess.check_call(shlex.split('launchctl start {namespace}.{program}'.format(**settings)))

def handle(**settings):
    assert('namespace' in settings)
    assert('vendor' in settings)
    assert('program' in settings)
    settings['run_folder'] = os.path.abspath(os.path.dirname(__file__))
    settings['application_folder'] = os.path.abspath(os.path.expanduser('~/Library/Application Support/{vendor}'.format(**settings)))
    settings['launchd_folder'] = os.path.abspath('/System/Library/LaunchAgents')
    settings['plist_filename'] = os.path.join(settings['launchd_folder'], '.'.join([settings['namespace'], settings['program'], 'plist']))

    commands = (sys.argv[1:] if len(sys.argv) > 1 else ['install', 'run'])
    for command in commands:
        if command == 'uninstall':
            uninstall(settings=settings)
        elif command == 'install':
            if not installed(settings=settings):
                install(settings=settings, packages={
                    # importable name : installable name
                    'Growl':'py-Growl',
                })
        elif command == 'run':
            run(settings=settings)
        elif command == 'restart':
            restart(settings=settings)