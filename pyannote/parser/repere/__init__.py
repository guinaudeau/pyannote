#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012 Herve BREDIN (bredin@limsi.fr)

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

"""
This module contains parser for common file formats used in the REPERE challenge (2011-2013).
See http://www.defi-repere.fr/
"""

__all__ = ['REPEREParser', 'TRSParser', 'XGTFParser', 'get_show_name']

from repere import REPEREParser
from trs import TRSParser
from xgtf import XGTFParser

def get_show_name(uri):
    """
    
    Parameters
    ----------
    uri : str
        Uniform Resource Identifier
    
    Returns
    -------
    show : str
        Name of the show
    
    Examples
    --------
    
        >>> print get_show_name('BFMTV_PlaneteShowbiz_20110705_195500')
        BFMTV_PlaneteShowbiz
    
    """
    tokens = uri.split('_')
    channel = tokens[0]
    show = tokens[1]
    return channel + '_' + show

if __name__ == "__main__":
    import doctest
    doctest.testmod()
