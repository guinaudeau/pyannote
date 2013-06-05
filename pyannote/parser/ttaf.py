# !/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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

from lxml import objectify
from pyannote.base.segment import Segment
from base import BaseAnnotationParser


class TTAFParser(BaseAnnotationParser):

    def __init__(self):
        super(TTAFParser, self).__init__()

    def timeToSeconds(self, t):
        """00:01:40.285 --> float(100.285)"""
        items = t.split(':')
        return float(items[-1]) + 60*int(items[-2]) + 3600*int(items[-3])
        return items

    def read(self, path, uri=None, **kwargs):

        root = objectify.parse(path).getroot()
        for p in root.body.div.p:
            start = p.attrib['begin']
            end = p.attrib['end']
            start = self.timeToSeconds(start)
            end = self.timeToSeconds(end)
            segment = Segment(start=start, end=end)
            for s, span in enumerate(p.span):
                track = 'line%d' % s
                text = span.text.strip().encode('utf-8')
                color = span.attrib['{http://www.w3.org/2006/10/ttaf1#style}color']
                self._add(segment, track, text, uri, 'subtitles')
                self._add(segment, track, color, uri, 'color')
        return self

if __name__ == "__main__":
    import doctest
    doctest.testmod()
