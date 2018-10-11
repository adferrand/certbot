import sys

from setuptools import setup
from setuptools import find_packages

version = '1.0'

setup(
    name='certbot-windows-utils',
    version=version,
    description="Various utilities for Certbot on Windows",
    url='https://github.com/certbot/certbot',
    author="Certbot Project",
    author_email='client-dev@letsencrypt.org',
    license='Apache License 2.0',
    python_requires='>=3.4',
    classifiers=[
        'Development Status :: 2 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Security',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities',
    ],
    packages=find_packages(),
    include_package_data=True,
)
