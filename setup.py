from __future__ import with_statement

from setuptools import setup, find_packages

from thredds_crawler import __version__


def readme():
    with open('README.md') as f:
        return f.read()

reqs = [line.strip() for line in open('requirements.txt')]

setup(
    name                = "thredds_crawler",
    version             = __version__,
    description         = "A Python library for crawling THREDDS servers",
    long_description    = readme(),
    license             = 'GPLv3',
    author              = "Kyle Wilcox",
    author_email        = "kyle@axiomdatascience.com",
    url                 = "https://github.com/asascience-open/thredds_crawler",
    packages            = find_packages(),
    install_requires    = reqs,
    classifiers         = [
            'Development Status :: 5 - Production/Stable',
            'Intended Audience :: Developers',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
            'Operating System :: OS Independent',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering',
        ],
    include_package_data = True,
) 
