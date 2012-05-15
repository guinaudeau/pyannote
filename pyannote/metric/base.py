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

class BaseErrorRate(object):
    
    def __init__(self, name, values):
        super(BaseErrorRate, self).__init__()
        self.__name = name
        self.__values = set(values)
        self.__details = self.init_details()

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
        rate = self.get_rate(detail)
        if detailed:
            detail = dict(detail)
            detail.update({self.__name: rate})
            return detail
        else:
            return rate
    
    def __call__(self, reference, hypothesis, detailed=False, **kwargs):
        detail = self.get_details(reference, hypothesis, **kwargs)
        return self.__compute(detail, accumulate=True, detailed=detailed)

    def __str__(self):
        detail = self.__compute(self.__details, \
                                accumulate=False, \
                                detailed=True)
        return self.pretty(detail)
    
    def __abs__(self):
        return self.get_rate(self.__details)
    
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
        
    def init_details(self):
        detail = {value: 0. for value in self.__values}
        return detail

    def get_details(self, reference, hypothesis, **kwargs):
        raise NotImplementedError('')
        
    def get_rate(self, detail):
        raise NotImplementedError('')
    
    def pretty(self, detail):
        raise NotImplementedError('')


PRECISION_NAME = 'precision'
PRECISION_RETRIEVED = '# retrieved'
PRECISION_RELEVANT_RETRIEVED = '# relevant retrieved'

class Precision(BaseErrorRate):
    def __init__(self):
        values = set([PRECISION_RETRIEVED, \
                      PRECISION_RELEVANT_RETRIEVED])
        super(Precision, self).__init__(PRECISION_NAME, values)
    
    def get_rate(self, detail):
        numerator = detail[PRECISION_RELEVANT_RETRIEVED] 
        denominator = detail[PRECISION_RETRIEVED]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                raise ValueError('')
        else:
            return numerator/denominator
    
    def pretty(self, detail):
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

class Recall(BaseErrorRate):
    def __init__(self):
        values = set([RECALL_RELEVANT, \
                      RECALL_RELEVANT_RETRIEVED])
        super(Recall, self).__init__(RECALL_NAME, values)
    
    def get_rate(self, detail):
        numerator = detail[RECALL_RELEVANT_RETRIEVED] 
        denominator = detail[RECALL_RELEVANT]
        if denominator == 0.:
            if numerator == 0:
                return 1.
            else:
                raise ValueError('')
        else:
            return numerator/denominator
    
    def pretty(self, detail):
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
