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

class REPEREParser(GenericParser):
    """
    .repere file parser
    """
    def __init__(self, path2repere, confidence=True, multitrack=False):
        # source start end modality identifier confidence
        if confidence:
            format = '{VIDEO} {START} {END} {MODALITY} {ID} {CONFIDENCE}'
        else:
            format = '{VIDEO} {START} {END} {MODALITY} {ID}'
        super(REPEREParser, self).__init__(path2repere, \
                                         format, \
                                         multitrack = multitrack)




# def toREPERE(annotation, confidence=False):
#     """"""
#     modality = annotation.modality
#     video    = annotation.video
#     text = ''
#     annotation = abs(annotation)
#     for s, segment in enumerate(annotation):
#         start = segment.start
#         end = segment.end
#         for i, identifier in enumerate(annotation.identifiers(segment=segment)):
#             if confidence:
#                 score = annotation.confidence(segment, identifier)
#                 # source start end modality identifier confidence
#                 text += '%s %g %g %s %s %g\n' % (video, start, end, modality, identifier, score)
#             else:
#                 text += '%s %g %g %s %s\n' % (video, start, end, modality, identifier)
#     return text


if __name__ == "__main__":
    import doctest
    doctest.testmod()
