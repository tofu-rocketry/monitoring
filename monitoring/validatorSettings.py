"""
Settings for the validator app, part of the monitoring project.

These settings are for the apel modules, so they need to be kept separate
from Django's control. Because Django was having issues with some of
the defined configuration, such as the database engine.
"""

import configparser
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    # Read configuration from the file
    cp = configparser.ConfigParser(interpolation=None)
    file_path = os.path.join(BASE_DIR, 'monitoring', 'settings.ini')
    cp.read(file_path)

    VALIDATOR_DB = {
        'ENGINE': cp.get('db_validator', 'backend'),
        'HOST': cp.get('db_validator', 'hostname'),
        'PORT': cp.get('db_validator', 'port'),
        'NAME': cp.get('db_validator', 'name'),
        'USER': cp.get('db_validator', 'username'),
        'PASSWORD': cp.get('db_validator', 'password'),
    }

except (configparser.NoSectionError) as err:
    print("Error in configuration file. Check that file exists first: %s" % err)
    sys.exit(1)
