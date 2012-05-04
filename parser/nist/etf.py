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

from ..generic import GenericParser

class ETF0Parser(GenericParser):
    """
    .etf0 file parser
    """
    def __init__(self, path2etf0):
        
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {NA} {ID} {CONFIDENCE} {NA}' 
        super(ETF0Parser, self).__init__(path2etf0, \
                                         format, \
                                         multitrack = False)

class ETFParser(GenericParser):
    """
    .etf file parser
    """
    def __init__(self, path2etf):
        
        format = '{VIDEO} {NA} {START} {DURATION} {MODALITY} {NA} {ID} {CONFIDENCE} {NA}' 
        super(ETFParser, self).__init__(path2etf, \
                                         format, \
                                         multitrack = False)


# def toETF(annotation):
#     """"""
#     modality = annotation.modality
#     video    = annotation.video
#     text = ''
#     for s, segment in enumerate(annotation):
#         start = segment.start
#         duration = segment.duration
#         for i, identifier in enumerate(annotation.identifiers(segment=segment)):
#             confidence = annotation.confidence(segment, identifier)
#             # source 1 start duration type subtype event [score [decision]]
#             text += '%s 1 %g %g %s - %s %g -\n' % (video, start, duration, modality, identifier, confidence)
#     return text

if __name__ == "__main__":
    import doctest
    doctest.testmod()

