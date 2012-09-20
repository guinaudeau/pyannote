#!/usr/bin/env python
# encoding: utf-8

from setuptools import setup, find_packages

setup(
    name='PyAnnote',
    version='0.2.2',
    description='Python module for collaborative annotation of multimedia content',
    author='Hervé Bredin',
    author_email='bredin@limsi.fr',
    url='http://packages.python.org/PyAnnote',
    # packages= find_packages(),
    packages=['pyannote', 
              'pyannote.base',
              'pyannote.algorithm',
              'pyannote.algorithm.mapping',
              'pyannote.algorithm.tagging',
              'pyannote.metric',
              'pyannote.parser',
              'pyannote.parser.repere',
              'pyannote.parser.nist'],
    install_requires=['numpy >=1.6.1', 
                      'scipy >=0.10.1',
                      'munkres >=1.0.5', 
                      'scikit-learn >=0.12',
                      'networkx >=1.6',
                      'lxml >=2.3.4',
                      'prettytable >=0.6',
                      'python-Levenshtein >=0.10.2'],
    classifiers=[ 
       "Development Status :: 4 - Beta", 
       "Intended Audience :: Science/Research", 
       "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)", 
       "Natural Language :: English", 
       "Programming Language :: Python :: 2.7", 
       "Topic :: Scientific/Engineering"]
)
