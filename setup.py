#!/bin/env python
"""
Setuptools file for workday
"""
from setuptools import (
    setup,
    find_packages,
)
from workday import __version__

setup(
    name='workday',
    author='marhag87',
    author_email='marhag87@gmail.com',
    url='https://github.com/marhag87/workday',
    version=__version__,
    packages=find_packages(),
    license='WTFPL',
    description='Keep track of your workday time',
    long_description='A module that keeps track of how long you have worked and when you can go home.',
    install_requires=[
        'pyyamlconfig',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3.7',
    ],
    scripts=['workday/workday.py'],
)
