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

from pyannote.base.segment import Segment
from pyannote.base import URI, TRACK, LABEL, SCORE
from base import BaseTextualScoresParser, BaseTextualFormat


class TVMMixin(BaseTextualFormat):

    START = 'start'
    DURATION = 'duration'

    def get_comment(self):
        return None

    def get_separator(self):
        return '[ \t]+'

    def get_fields(self):
        return [URI,
                self.START,
                self.DURATION,
                TRACK,
                LABEL,
                SCORE]

    def get_default_modality(self):
        return "head"

    def get_segment(self, row):
        return Segment(row[self.START], row[self.START]+row[self.DURATION])

    def get_converters(self):
        # 'head_52' ==> '52'
        #return {TRACK: lambda x: x.split('_')[1]}
        return None

    def _append(self, scores, f, uri, modality):
        try:
            format = '%s %%g %%g %s %%s %%g\n' % (uri, modality)
            for segment, track, label, value in scores.itervalues():
                f.write(format % (segment.start, segment.end,
                                  label, value))
        except Exception, e:
            print "Error @ %s%s %s %s" % (uri, segment, track, label)
            raise e


class TVMParser(BaseTextualScoresParser, TVMMixin):
    pass
