#!/usr/bin/env python
from setuptools import find_packages, setup

setup(
    name='monitoring',
    version='0.2',
    packages=find_packages(),
    scripts=['manage.py'],
)
