#!/usr/bin/env python
# encoding: utf-8

from pyannote.algorithms.association.hungarian import hungarian
from identification import IdentificationErrorRate, IER_CONFUSION, IER_FALSE_ALARM, IER_MISS, IER_TOTAL, IER_CORRECT

DER_CONFUSION = IER_CONFUSION
DER_FALSE_ALARM = IER_FALSE_ALARM
DER_MISS = IER_MISS
DER_TOTAL = IER_TOTAL
DER_CORRECT = IER_CORRECT
DER_NAME = 'diarization error rate'

class DiarizationErrorRate(IdentificationErrorRate):
    
    def __init__(self):

        numerator = {DER_CONFUSION: 1., \
                     DER_FALSE_ALARM: 1., \
                     DER_MISS: 1., }
        
        denominator = {DER_TOTAL: 1., }
        other = [DER_CORRECT]
        super(IdentificationErrorRate, self).__init__(DER_NAME, numerator, denominator, other)
    
    def __call__(self, reference, hypothesis, detailed=False):
        
        mapping = hungarian(hypothesis, reference)
        return super(DiarizationErrorRate, self).__call__(reference, hypothesis % mapping, detailed=detailed)

