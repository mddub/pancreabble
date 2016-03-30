# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

import pancreabble
setup(
    name='pancreabble',
    version=pancreabble.__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=["libpebble2", ],
    scripts = [

    ]
)
