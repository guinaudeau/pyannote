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
Module :mod:`pyannote.metric.diarization` defines evaluation metric for the diarization/clustering task.
"""

from pyannote.algorithm.mapping.hungarian import HungarianMapper

from identification import IdentificationErrorRate, \
                           IER_CONFUSION, \
                           IER_FALSE_ALARM, \
                           IER_MISS, \
                           IER_TOTAL, \
                           IER_CORRECT


DER_NAME = 'diarization error rate'


class DiarizationErrorRate(IdentificationErrorRate):
    """Diarization error rate
    
    First, the optimal mapping between reference and hypothesis labels
    is obtained using the Hungarian algorithm. Then, the actual diarization 
    error rate is computed as the identification error rate with each hypothesis
    label trasnlated into the corresponding reference label.
    
    * Diarization error rate between `reference` and `hypothesis` annotations
        
        >>> metric = DiarizationErrorRate()
        >>> reference = Annotation(...)           # doctest: +SKIP
        >>> hypothesis = Annotation(...)          # doctest: +SKIP
        >>> value = metric(reference, hypothesis) # doctest: +SKIP
        
    * Compute global diarization error rate and confidence interval 
      over multiple documents
        
        >>> for reference, hypothesis in ...      # doctest: +SKIP
        ...    metric(reference, hypothesis)      # doctest: +SKIP
        >>> global_value = abs(metric)            # doctest: +SKIP
        >>> mean, (lower, upper) = metric.confidence_interval() # doctest: +SKIP
        
    * Get diarization error rate detailed components
        
        >>> components = metric(reference, hypothesis, detailed=True) #doctest +SKIP
        
    * Get accumulated components
        
        >>> components = metric[:]                # doctest: +SKIP
        >>> metric['confusion']                   # doctest: +SKIP
    
    See Also
    --------
    :class:`pyannote.metric.base.BaseMetric`: details on accumumation
    :class:`pyannote.metric.identification.IdentificationErrorRate`: identification error rate
    
    """
    def __init__(self):
        super(DiarizationErrorRate, self).__init__()
        self.name = DER_NAME
        self.__hungarian = HungarianMapper()
    
    def optimal_mapping(self, reference, hypothesis):
        """Optimal label mapping"""
        return self.__hungarian(hypothesis, reference)
    
    def _get_details(self, reference, hypothesis, **kwargs):
        mapping = self.optimal_mapping(reference, hypothesis)
        return super(DiarizationErrorRate, self)._get_details(reference, \
                                                         hypothesis % mapping)

from base import BaseMetric
from pyannote.base.matrix import Cooccurrence
import numpy as np

PURITY_NAME = 'purity'
PURITY_TOTAL = 'total'
PURITY_CORRECT = 'correct'

class DiarizationPurity(BaseMetric):
    """Purity"""
    def __init__(self):
        values = set([ \
            PURITY_TOTAL, \
            PURITY_CORRECT])
        super(DiarizationPurity, self).__init__(PURITY_NAME, values)
    
    def _get_details(self, reference, hypothesis, **kwargs):
        detail = self._init_details()
        matrix = Cooccurrence(reference, hypothesis)
        
        if np.prod(matrix.M.shape):
            detail[PURITY_CORRECT] = np.sum(np.max(matrix.M, axis=0))
        else:
            detail[PURITY_CORRECT] = 0.
        
        detail[PURITY_TOTAL] = np.sum(matrix.M)
        
        return detail
    
    def _get_rate(self, detail):
        if detail[PURITY_TOTAL] > 0.:
            return detail[PURITY_CORRECT] / detail[PURITY_TOTAL]
        else:
            return 1.
       
    def _pretty(self, detail):
        string = ""
        string += "  - duration: %.2f seconds\n" % (detail[PURITY_TOTAL])
        string += "  - correct: %.2f seconds\n" % (detail[PURITY_CORRECT])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

COVERAGE_NAME = 'coverage'

class DiarizationCoverage(DiarizationPurity):
    """Coverage"""
    def __init__(self):
        super(DiarizationCoverage, self).__init__()
        self.name = COVERAGE_NAME
    
    def _get_details(self, reference, hypothesis, **kwargs):
        return super(DiarizationCoverage, self)._get_details(hypothesis, \
                                                            reference)

HOMOGENEITY_NAME = 'homogeneity'
HOMOGENEITY_ENTROPY = 'entropy'
HOMOGENEITY_CROSS_ENTROPY = 'cross-entropy'

class DiarizationHomogeneity(BaseMetric):
    """Homogeneity"""
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
        for i, ilabel in enumerate(matrix.iter_ilabels()):
            ratio = rduration[i] / duration
            if ratio > 0:
                entropy -= ratio * np.log(ratio)
            for j, jlabel in enumerate(matrix.iter_jlabels()):
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
    """Completeness"""
    def __init__(self):
        super(DiarizationCompleteness, self).__init__()
        self.name = COMPLETENESS_NAME
    
    def _get_details(self, reference, hypothesis, **kwargs):
        return super(DiarizationCompleteness, self)._get_details(hypothesis, \
                                                            reference)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
