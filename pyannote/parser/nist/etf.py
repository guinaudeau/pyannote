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

import numpy as np
from pyannote.parser.base import BaseTextualFormat, BaseTextualScoresParser
from pyannote import Segment
from pyannote.base import URI, MODALITY, TRACK, LABEL, SCORE


class ETF0Mixin(BaseTextualFormat):
    
    CHANNEL = 'channel'
    START = 'start'
    DURATION = 'duration'
    
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
                TRACK,
                LABEL,
                SCORE,
                'X']
    
    def get_segment(self, row):
        return Segment(row[self.START], row[self.START]+row[self.DURATION])
    
    def _append(self, scores, f, uri, modality):
        
        # create new annotation with top-score label
        annotation = scores.to_annotation(threshold=-np.inf)
        
        try:
            format = '%s 1 %%g %%g %s %%s %%s %%g %%s\n' % (uri, modality)
            for s,t,l,v in scores.itervalues():
                status = 'top_score' if annotation[s,t] == l else '-'
                f.write(format % (s.start, s.duration, t, l, v, status))
        except Exception, e:
            print "Error @ %s %s %s %s" % (uri, s, t, l)
            raise e
    

class ETF0Parser(BaseTextualScoresParser, ETF0Mixin):
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()

