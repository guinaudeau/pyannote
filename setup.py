#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

# This file is part of PyAnnote.
#
#     PyAnnote is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     PyAnnote is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with PyAnnote.  If not, see <http://www.gnu.org/licenses/>.


# from setuptools import setup, find_packages
from setuptools import setup

setup(
    name='PyAnnote',
    version='0.3',
    description=(
        'Python module for collaborative annotation '
        'of multimedia content'
    ),
    author='Hervé Bredin',
    author_email='bredin@limsi.fr',
    url='http://packages.python.org/PyAnnote',
    # packages= find_packages(),
    packages=['pyannote',
              'pyannote.algorithm.mapping'],
    #           'pyannote.base',
    #           'pyannote.algorithm',
    #           'pyannote.algorithm.mapping',
    #           'pyannote.algorithm.tagging',
    #           'pyannote.metric',
    #           'pyannote.parser',
    #           'pyannote.parser.repere',
    #           'pyannote.parser.nist'],
    install_requires=[
        'numpy >=1.7.1',
        'scipy >=0.13.0',
        'banyan >=0.1.5',
        'pandas >=0.12.0',
        'munkres >=1.0.5.4',
        'decorator >=3.4.0',
        'networkx >=1.8.1',
        'scikit-learn >=0.14',
        'joblib >=0.7.1',
        'pysrt >=0.5.0'
        # 'lxml >=2.3.4'],
        #'prettytable >=0.6',
        #'python-Levenshtein >=0.10.2'],
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Natural Language :: English",
        "Programming Language :: Python :: 2.7",
        "Topic :: Scientific/Engineering"]
)
