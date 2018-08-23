#!/usr/bin/env python

from setuptools import setup, find_packages
from importlib import import_module
import json

if __name__ == '__main__':
    # Provide static information in setup.json
    # such that it can be discovered automatically
    with open('setup.json', 'r') as info:
        kwargs = json.load(info)
    kwargs["version"] = import_module('aiida_crystal17').__version__
    setup(
        packages=find_packages(),
        **kwargs
    )
