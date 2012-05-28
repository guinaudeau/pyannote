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

from pyannote.algorithm.mapping.hungarian import HungarianMapper

from identification import IdentificationErrorRate, \
                           IER_CONFUSION, \
                           IER_FALSE_ALARM, \
                           IER_MISS, \
                           IER_TOTAL, \
                           IER_CORRECT

# from prettytable import PrettyTable
# class DiarizationReport(object):
#     
#     def __init__(self, name, values):
#         super(BaseErrorRate, self).__init__()
#         self.__err_rates = {'DER' : DiarizationErrorRate(), 
#                             'Purity' : DiarizationPurity(),
#                             'Coverage' : DiarizationCoverage(),
#                             'Homogeneity' : DiarizationHomogeneity(), 
#                             'Completeness' : DiarizationCompleteness()}
#     
#     def reset(self):
#         for err_rate in self.__err_rates.itervalues():
#             err_rate.reset()
#     
#     def __call__(self, reference, hypothesis, **kwargs):
#         return {err_rate.name : err_rate(reference, hypothesis, 
#                                          detailed=False, **kwargs) 
#                 for err_rate in self.__err_rates.itervalues()}
#     
#     def __abs__(self):
#         return {err_rate.name : abs(err_rate) 
#                 for err_rate in self.__err_rates.itervalues()}
#     
#     def confidence_interval(self, alpha=0.9):
#         return {err_rate.name : err_rate.confidence_interval(alpha=alpha) 
#                 for err_rate in self.__err_rates.itervalues()}
#     
#     def report(self, uri='URI', float_format='1.3'):
#         
#         if uri is None:
#             uri = 'URI'
#         
#         
#         table = PrettyTable()
#         table.add_column(uri, [v for v,_ in self.__err_rates['DER']], align='l')
#         
#         for name, err_rate in self.__err_rates.iteritems():
#             table.add_column(name, [r for _,r in err_rate], align='c')
#             table.float_format[name] = float_format
#         
#         
#         # 90% confidence interval | 0.123 < 0.345 < 0.567
#         fmt = '%%sf < %%sf < %%sf' % (float_format, float_format, float_format)
#         m, (l, u) = self.confidence_interval(alpha=0.9)
#         table.add_row(['     90% confidence interval', fmt % (l, m, u)])
#         
#         return table

DER_NAME = 'diarization error rate'

class DiarizationErrorRate(IdentificationErrorRate):
    
    def __init__(self):
        super(DiarizationErrorRate, self).__init__()
        self.name = DER_NAME
        self.__hungarian = HungarianMapper()
    
    def _get_details(self, reference, hypothesis, **kwargs):
        mapping = self.__hungarian(hypothesis, reference)
        return super(DiarizationErrorRate, self)._get_details(reference, \
                                                         hypothesis % mapping)

from base import BaseErrorRate
from pyannote.base.matrix import Cooccurrence
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
    
    def _get_details(self, reference, hypothesis, **kwargs):
        detail = self._init_details()
        matrix = Cooccurrence(reference, hypothesis)
        detail[PURITY_CORRECT] = np.sum(np.max(matrix.M, axis=0))
        detail[PURITY_TOTAL] = np.sum(matrix.M)
        return detail
    
    def _get_rate(self, detail):
        numerator = 1. * detail[PURITY_CORRECT]
        denominator = 1. * detail[PURITY_TOTAL]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                return 1.
        else:
            return numerator/denominator
       
    def _pretty(self, detail):
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
    
    def _get_details(self, reference, hypothesis, **kwargs):
        return super(DiarizationCoverage, self)._get_details(hypothesis, \
                                                            reference)

HOMOGENEITY_NAME = 'homogeneity'
HOMOGENEITY_ENTROPY = 'entropy'
HOMOGENEITY_CROSS_ENTROPY = 'cross-entropy'

class DiarizationHomogeneity(BaseErrorRate):
    
    def __init__(self):
        values = set([ \
            HOMOGENEITY_ENTROPY, \
            HOMOGENEITY_CROSS_ENTROPY])
        super(DiarizationHomogeneity, self).__init__(HOMOGENEITY_NAME, values)
    
    def _get_details(self, reference, hypothesis, **kwargs):
        detail = self._init_details()
            
        matrix = Cooccurrence(reference, hypothesis)
        duration = np.sum(matrix.M)
        rduration = np.sum(matrix.M, axis=1)
        hduration = np.sum(matrix.M, axis=0)
            
        # Reference entropy and reference/hypothesis cross-entropy
        cross_entropy = 0.
        entropy = 0.
        for i, ilabel in matrix.iter_ilabels(index=True):
            ratio = rduration[i] / duration
            entropy -= ratio * np.log(ratio)                
            for j, jlabel in matrix.iter_jlabels(index=True):
                coduration = matrix[ilabel, jlabel]
                if coduration > 0:
                    cross_entropy -= (coduration / duration) * \
                                     np.log(coduration / hduration[j])
                        
        detail[HOMOGENEITY_CROSS_ENTROPY] = cross_entropy 
        detail[HOMOGENEITY_ENTROPY] = entropy
             
        return detail
    
    def _get_rate(self, detail):
        numerator = 1. * detail[HOMOGENEITY_CROSS_ENTROPY]
        denominator = 1. * detail[HOMOGENEITY_ENTROPY]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                return 0.
        else:
            return 1. - numerator/denominator
       
    def _pretty(self, detail):
        string = ""
        string += "  - %s: %.2f\n" % \
                  (HOMOGENEITY_ENTROPY, detail[HOMOGENEITY_ENTROPY])
        string += "  - %s: %.2f\n" % \
                  (HOMOGENEITY_CROSS_ENTROPY, \
                  detail[HOMOGENEITY_CROSS_ENTROPY])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

COMPLETENESS_NAME = 'completeness'

class DiarizationCompleteness(DiarizationHomogeneity):
    
    def __init__(self):
        super(DiarizationCompleteness, self).__init__()
        self.name = COMPLETENESS_NAME
    
    def _get_details(self, reference, hypothesis, **kwargs):
        return super(DiarizationCompleteness, self)._get_details(hypothesis, \
                                                            reference)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
