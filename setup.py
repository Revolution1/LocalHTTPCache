#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""
import os
import platform

try:  # for pip >= 10
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.req import parse_requirements

from setuptools import setup, find_packages

PY2 = platform.python_version_tuple()[0] == '2'

readme_path = 'README.md'
if os.path.isfile('README.rst'):
    readme_path = 'README.rst'
with open(readme_path) as readme_file:
    readme = readme_file.read()

install_reqs = parse_requirements('requirements.txt', session='')

# reqs is a list of requirement
requirements = [str(ir.req) for ir in install_reqs]

setup_requirements = [
    # 'pytest-runner',
]

setup(
    name='local-http-cache',
    version='0.0.1',
    description="Tool that helps you setting up a local proxy to cache static files",
    long_description=readme,
    author="Renjie Cai",
    author_email='revol.cai@gmail.com',
    url='https://github.com/Revolution1/LocalHTTPCache',
    packages=find_packages(include=['lhc*']),
    entry_points={
        'console_scripts': [
            'lhc=lhc.lhc:main'
        ]
    },
    include_package_data=True,
    install_requires=requirements,
    license="Apache Software License 2.0",
    python_requires='>=2.7, <3.0',
    zip_safe=False,
    keywords='LocalHTTPCache',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7'
    ],
    test_suite='tests',
    setup_requires=setup_requirements,
)
