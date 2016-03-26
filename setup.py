#!/usr/bin/env python

from setuptools import setup, find_packages

cfg = dict(
    name             = 'raspberry-api-server',
    version          = '0.1',
    description      = 'A RESTful API to the Raspberry Pi',
    packages         = find_packages(),
    zip_safe         = False,
    install_requires = [
        'rpi.gpio',
        'flask',
        'flask-restplus',
    ]
)

if __name__ == '__main__':
    setup(**cfg)
