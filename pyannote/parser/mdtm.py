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
MDTM (Meta Data Time-Mark) is a file format used to specify label
for time regions within a recorded waveform.
"""

from pyannote.base.segment import Segment
from pyannote.base import URI, MODALITY, LABEL
from base import BaseTextualFormat, BaseTextualAnnotationParser


class MDTMMixin(BaseTextualFormat):

    CHANNEL = 'channel'
    START = 'start'
    DURATION = 'duration'
    CONFIDENCE = 'confidence'
    GENDER = 'gender'

    def get_comment(self):
        return ';'

    def get_separator(self):
        return ' '

    def get_fields(self):
        return [URI,
                self.CHANNEL,
                self.START,
                self.DURATION,
                MODALITY,
                self.CONFIDENCE,
                self.GENDER,
                LABEL]

    def get_segment(self, row):
        return Segment(row[self.START], row[self.START]+row[self.DURATION])

    def _append(self, annotation, f, uri, modality):

        try:
            format = '%s 1 %%g %%g %s NA %%s %%s\n' % (uri, modality)
            for segment, track, label in annotation.itertracks(label=True):
                f.write(format % (segment.start, segment.duration,
                                  track, label))
        except Exception, e:
            print "Error @ %s%s %s %s" % (uri, segment, track, label)
            raise e


class MDTMParser(BaseTextualAnnotationParser, MDTMMixin):
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
