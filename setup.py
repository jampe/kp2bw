#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as requirements_file:
    requirements = [line.replace("\n", "") for line in requirements_file.readlines()]

setup(
    name='kp2bw',
    version='1.0',
    description="Imports and existing KeePass db with REF fields into Bitwarden",
    python_requires=">=3.0",
    long_description=readme,
    author="Daniel Jampen",
    author_email='daniel@jampen.net',
    url='https://github.zhaw.ch/jampe/kp2bw',
    packages=[
        'kp2bw',
    ],
    package_dir={'kp2bw': '.'},
    include_package_data=True,
    install_requires=requirements,
    zip_safe=False,
    keywords='presenter',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.7',
    ],
)
