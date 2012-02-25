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

from pyannote.algorithms.association.hungarian import Hungarian
from identification import IdentificationErrorRate, \
                           IER_CONFUSION, \
                           IER_FALSE_ALARM, \
                           IER_MISS, \
                           IER_TOTAL, \
                           IER_CORRECT

DER_NAME = 'diarization error rate'

class DiarizationErrorRate(IdentificationErrorRate):
    
    def __init__(self):
        super(DiarizationErrorRate, self).__init__()
        self.name = DER_NAME
        self.__hungarian = Hungarian()
    
    def get_details(self, reference, hypothesis):
        mapping = self.__hungarian(hypothesis, reference)
        return super(DiarizationErrorRate, self).get_details(reference, \
                                                         hypothesis % mapping)

