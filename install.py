#!/usr/bin/env python

# Only import default Python packages here.  You can't depend on any other packages being present at this point in the script execution.
import os
import os.path
import shlex
import shutil
import subprocess
import sys

VENDOR = 'Bornski'
PROGRAM = 'Growl Demo'
CONFIG = {
    'run_folder':os.path.abspath(os.path.dirname(__file__)),
    'application_folder':os.path.abspath(os.path.expanduser('~/Library/Application Support/{vendor}'.format(vendor=VENDOR))),
    'launchd_folder':os.path.abspath('/System/Library/LaunchAgents'),
    'namespace':'com.{vendor}'.format(vendor=VENDOR.lower()),
    'application_name':'{program}'.format(program=''.join(PROGRAM.split())),
}
# Absolute filenames
CONFIG['application_icon'] = os.path.join(CONFIG['run_folder'], 'heart_tattoo.png')
# Relative filenames
CONFIG['plist_filename'] = os.path.join(CONFIG['launchd_folder'], '.'.join([CONFIG['namespace'], CONFIG['application_name'], 'plist']))
CONFIG['bash_filename'] = CONFIG['application_name']

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
        os.execv(os.path.abspath(__file__), sys.argv)

def installed():
    # Check that the application folder exists and that the launchd configuration is valid.
    return (subprocess.call(shlex.split('launchctl list {namespace}.{application_name}'.format(**CONFIG))) == 0)

def uninstall():
    bootstrap({'shmac':'git+http://github.com/mattbornski/shmac.git#egg=shmac'})
    import shmac
    
    # Remove config from launchd and remove the application folder.
    try:
        subprocess.call(shlex.split('launchctl unload {plist_filename}'.format(**CONFIG)))
    except OSError:
        pass
    shmac.sudo('rm {plist_filename}'.format(**CONFIG))
    try:
        shutil.rmtree(CONFIG['application_folder'])
    except OSError:
        pass

def install(packages={}):
    bootstrap({'shmac':'git+http://github.com/mattbornski/shmac.git#egg=shmac'})
    import shmac
    
    # Create the environment necessary to run our application
    cwd = os.getcwd()
    try:
        shutil.copytree(CONFIG['run_folder'], CONFIG['application_folder'], ignore=lambda src, names: [n for n in names if n in ['.git', '.gitignore']])
        os.chdir(CONFIG['application_folder'])
        if len(packages) > 0:
            try:
                import virtualenv
            except ImportError:
                subprocess.check_call(shlex.split('pip install virtualenv --user'))
            subprocess.check_call(shlex.split('virtualenv --no-site-packages env'))
            subprocess.check_call(shlex.split('pip install ' + ' '.join(packages.values()) + ' -E env'))
        with open(CONFIG['bash_filename'], 'w') as bash:
            bash.write('''#!/bin/bash
{virtualenv}
echo "import {application_name} ; {application_name}.run()" | /usr/bin/env python -
'''.format(virtualenv='source env/bin/activate\n' if len(packages) > 0 else '', **CONFIG))
        os.chmod(CONFIG['bash_filename'], 0755)
        
        # Create the launchd file for our application
        temp_plist_filename = os.path.basename(CONFIG['plist_filename'])
        with open(temp_plist_filename, 'w') as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>{namespace}.{application_name}</string>
    <key>Program</key>
    <string>{application_folder}/{application_name}</string>
    <key>WorkingDirectory</key>
    <string>{application_folder}</string>
    <key>ProgramArguments</key>
    <array>
      <string>{application_name}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{application_folder}/{application_name}.log</string>
    <key>StandardErrorPath</key>
    <string>{application_folder}/{application_name}.log</string>
  </dict>
</plist>'''.format(**CONFIG))
        shmac.sudo('cp {temp_plist_filename} {plist_filename}'.format(temp_plist_filename=temp_plist_filename, **CONFIG))
        os.remove(temp_plist_filename)
    finally:
        os.chdir(cwd)

def run():
    # Ask launchd to start the program.
    subprocess.check_call(shlex.split('launchctl load {plist_filename}'.format(**CONFIG)))
    subprocess.check_call(shlex.split('launchctl start {namespace}.{application_name}'.format(**CONFIG)))

if __name__ == '__main__':
    commands = (sys.argv[1:] if len(sys.argv) > 1 else ['install', 'run'])
    for command in commands:
        if command == 'uninstall':
            uninstall()
        elif command == 'install':
            if not installed():
                install(packages={})
        elif command == 'run':
            run()