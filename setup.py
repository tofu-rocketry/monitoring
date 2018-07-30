#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='monitoring',
    version='0.1',
    packages=find_packages(),
    scripts=['manage.py'],
)
