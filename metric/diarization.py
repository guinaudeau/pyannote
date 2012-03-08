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

from base import BaseErrorRate
from pyannote.base.comatrix import Confusion
import numpy as np

PURITY_NAME = 'purity'
PURITY_TOTAL = 'total'
PURITY_CORRECT = 'correct'

class DiarizationPurity(BaseErrorRate):
    
    def __init__(self):
        values = set([ \
            PURITY_TOTAL, \
            PURITY_CORRECT])
        super(DiarizationPurity, self).__init__(PURITY_NAME, values)
    
    def get_details(self, reference, hypothesis, **kwargs):
        detail = self.init_details()
        matrix = Confusion(reference, hypothesis, normalize=False)        
        detail[PURITY_CORRECT] = np.sum(np.max(matrix.M, axis=0))
        detail[PURITY_TOTAL] = np.sum(matrix.M)
        return detail
    
    def get_rate(self, detail):
        numerator = 1. * detail[PURITY_CORRECT]
        denominator = 1. * detail[PURITY_TOTAL]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                return 1.
        else:
            return numerator/denominator
       
    def pretty(self, detail):
        string = ""
        string += "  - duration: %.2f seconds\n" % (detail[PURITY_TOTAL])
        string += "  - correct: %.2f seconds\n" % (detail[PURITY_CORRECT])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

COVERAGE_NAME = 'coverage'

class DiarizationCoverage(DiarizationPurity):
    
    def __init__(self):
        super(DiarizationCoverage, self).__init__()
        self.name = COVERAGE_NAME
    
    def get_details(self, reference, hypothesis, **kwargs):
        return super(DiarizationCoverage, self).get_details(hypothesis, \
                                                            reference)
