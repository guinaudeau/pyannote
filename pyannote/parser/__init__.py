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

from nist import *
from repere import *
from other import *
from feature import *

class Parser(object):
    
    def __guess(self, extension):
        guess = {
            # '.plp':    PLPParser, 
            '.mdtm':   MDTMParser,
            '.uem':    UEMParser,
            # '.lst':    LSTParser, 
            '.seg':    SEGParser,
            '.repere': REPEREParser,
            '.trs':    TRSParser, 
            '.xgtf':   XGTFParser, 
        }
        return guess.get(extension, None)
    
    def __init__(self):
        super(Parser, self).__init__()
        self.__parser = None
    
    def __get_videos(self):
        return self.__parser.videos
    videos = property(fget=__get_videos)
    
    def __get_modalities(self):
        return self.__parser.modalities
    modalities = property(fget=__get_modalities)
    
    def read(self, path, video=None, modality=None, **kwargs):
        import os
        _, extension = os.path.splitext(path)
        GuessParser = self.__guess(extension)
        if GuessParser is None:
            raise NotImplementedError('unknown extension %s.' % extension)
        if self.__parser is None or not isinstance(self.__parser, GuessParser):
            self.__parser = GuessParser()
        self.__parser.read(path, video=video, modality=modality, **kwargs)
        return self
    
    def __call__(self, video=None, modality=None, **kwargs):
        return self.__parser(video=video, modality=modality, **kwargs)
    
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
