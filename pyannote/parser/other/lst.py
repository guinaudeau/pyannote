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


class LSTParser(object):
    def __init__(self):
        super(LSTParser, self).__init__()
    
    def read(self, path):
        """
        
        Parameters
        ----------
        path : str
            Path to list file (.lst)
            
        Returns
        -------
        lines : list
            List of stripped lines
        """
        lines = []
        f = open(path, 'r')
        lines = [line.strip() for line in f]
        f.close()
        return lines

if __name__ == "__main__":
    import doctest
    doctest.testmod()
