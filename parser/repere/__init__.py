#!/usr/bin/env python
# encoding: utf-8

"""
This module contains parser for common file formats used in the REPERE challenge (2011-2013).
See http://www.defi-repere.fr/
"""

__all__ = ['REPEREParser', 'TRSParser', 'XGTFParser']

from repere import REPEREParser
from trs import TRSParser
from xgtf import XGTFParser

