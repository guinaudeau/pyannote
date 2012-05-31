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

import scipy.stats
import numpy as np

class BaseMetric(object):
    """
    """
    def __init__(self, name, values):
        super(BaseMetric, self).__init__()
        self.__name = name
        self.__values = set(values)
        self.reset()
    
    def __get_name(self): 
        return self.__name
    def __set_name(self, name):
        self.__name = name
    name = property(fget=__get_name, \
                     fset=__set_name, \
                     fdel=None, \
                     doc="Metric name.")
    
    def __accumulate(self, detail):
        for value in self.__values:
            self.__details[value] += detail[value]
    
    def __compute(self, detail, accumulate=True, detailed=False):
        if accumulate:
            self.__accumulate(detail)
        rate = self._get_rate(detail)
        if detailed:
            detail = dict(detail)
            detail.update({self.__name: rate})
            return detail
        else:
            return rate
    
    def __call__(self, reference, hypothesis, detailed=False, **kwargs):
        detail = self._get_details(reference, hypothesis, **kwargs)
        self.__rates.append((reference.video, self._get_rate(detail)))
        return self.__compute(detail, accumulate=True, detailed=detailed)
    
    def __str__(self):
        detail = self.__compute(self.__details, \
                                accumulate=False, \
                                detailed=True)
        return self._pretty(detail)
    
    def __abs__(self):
        return self._get_rate(self.__details)
    
    def __getitem__(self, key):
        """Get specific detail value
        
        Use expression 'error['KEYWORD']' or 'error[:]'
        
        Parameters
        ----------
        key : str
            Name of a valid detail value.
        
        """
        if key == slice(None, None, None):
            return dict(self.__details)
        else:
            return self.__details[key]
    
    def __iter__(self):
        for v, r in self.__rates:
            yield v, r
    
    def _get_details(self, reference, hypothesis, **kwargs):
        raise NotImplementedError('')
        
    def _get_rate(self, detail):
        raise NotImplementedError('')
    
    def _pretty(self, detail):
        raise NotImplementedError('')
    
    def _init_details(self):
        return {value: 0. for value in self.__values}
    
    def reset(self):
        self.__details = self._init_details()
        self.__rates = []
    
    def confidence_interval(self, alpha=0.9):
        m,_,_ = scipy.stats.bayes_mvs([r for _,r in self.__rates], alpha=alpha)
        return m


PRECISION_NAME = 'precision'
PRECISION_RETRIEVED = '# retrieved'
PRECISION_RELEVANT_RETRIEVED = '# relevant retrieved'

class Precision(BaseMetric):
    def __init__(self):
        values = set([PRECISION_RETRIEVED, \
                      PRECISION_RELEVANT_RETRIEVED])
        super(Precision, self).__init__(PRECISION_NAME, values)
    
    def _get_rate(self, detail):
        numerator = detail[PRECISION_RELEVANT_RETRIEVED] 
        denominator = detail[PRECISION_RETRIEVED]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                raise ValueError('')
        else:
            return numerator/denominator
    
    def _pretty(self, detail):
        string = ""
        string += "  - %s: %d\n" % (PRECISION_RETRIEVED, \
                                    detail[PRECISION_RETRIEVED])
        string += "  - %s: %d\n" % (PRECISION_RELEVANT_RETRIEVED, \
                                    detail[PRECISION_RELEVANT_RETRIEVED])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

RECALL_NAME = 'recall'
RECALL_RELEVANT = '# relevant'
RECALL_RELEVANT_RETRIEVED = '# relevant retrieved'

class Recall(BaseMetric):
    def __init__(self):
        values = set([RECALL_RELEVANT, \
                      RECALL_RELEVANT_RETRIEVED])
        super(Recall, self).__init__(RECALL_NAME, values)
    
    def _get_rate(self, detail):
        numerator = detail[RECALL_RELEVANT_RETRIEVED] 
        denominator = detail[RECALL_RELEVANT]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                raise ValueError('')
        else:
            return numerator/denominator
    
    def _pretty(self, detail):
        string = ""
        string += "  - %s: %d\n" % (RECALL_RELEVANT, \
                                    detail[RECALL_RELEVANT])
        string += "  - %s: %d\n" % (RECALL_RELEVANT_RETRIEVED, \
                                    detail[RECALL_RELEVANT_RETRIEVED])
        string += "  - %s: %.2f %%\n" % (self.name, 100*detail[self.name])
        return string

def f_measure(precision, recall, beta=1.):
    return (1+beta*beta)*precision*recall / (beta*beta*precision+recall)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
