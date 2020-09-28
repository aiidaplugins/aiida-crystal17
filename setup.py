#!/usr/bin/env python

# from importlib import import_module
import json

from setuptools import find_packages, setup

if __name__ == "__main__":
    # Provide static information in setup.json
    # such that it can be discovered automatically
    with open("setup.json", "r") as info:
        kwargs = json.load(info)
    setup(
        packages=find_packages(),
        # version=import_module('aiida_crystal17').__version__,
        long_description=open("README.md").read(),
        long_description_content_type="text/markdown",
        **kwargs
    )
