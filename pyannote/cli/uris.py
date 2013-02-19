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

URI_PLACEHOLDER = '[URI]'
URI_SUPPORT = ' %s placeholder is supported.' % URI_PLACEHOLDER

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class BaseURIHandler(object):
    
    def __init__(self):
        super(BaseURIHandler, self).__init__()
        self.fromInput = set([])
        self.fromFilter = set([])
    
    def addFromInput(self, uris):
        self.fromInput.update(uris)
    
    def addFromFilter(self, uris):
        self.fromFilter.update(uris)
    
    def uris(self):
        if self.fromFilter:
            return sorted(self.fromFilter)
        else:
            return sorted(self.fromInput)

class URIHandler(BaseURIHandler):
    __metaclass__ = Singleton

