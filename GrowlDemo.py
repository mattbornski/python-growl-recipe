#!/usr/bin/env python

from __future__ import with_statement
import os.path

SETTINGS = {
    'namespace':'com.bornski',
    'vendor':'Bornski',
    'program':'GrowlDemo',
    'icon':os.path.join(os.path.dirname(__file__), 'icon.png'),
    # What non-default packages need to be installed?
    'packages':{
        'Growl':'py-Growl',
    },
    # Which function in this file should be called?
    'entry_point':'run',
}

def run():
    import Growl
    
    icon = open(SETTINGS['icon'], 'rb').read()
    notifier = Growl.GrowlNotifier(applicationName=SETTINGS['program'], notifications=['alive'], applicationIcon=icon)
    notifier.register()
    notifier.notify('alive', SETTINGS['program'], '<-- Now that\'s going to be a big growl')

import launchd
launchd.handle(**SETTINGS)