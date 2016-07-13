# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

__version__ = None
exec(open('pancreabble/version.py').read())

setup(
    name='pancreabble',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "libpebble2",
        "openaps",
        "tzlocal",
    ],
    scripts = [

    ]
)
