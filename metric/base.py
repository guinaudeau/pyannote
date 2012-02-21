#!/usr/bin/env python
# encoding: utf-8

class BaseErrorRate(object):
    
    def __init__(self, name, numerator, denominator, other=None):
        """
        numerator = {'false alarm': 1, 'miss': 1, 'confusion': 0.5}
        denominator = {'total': 1}
        other = ['correct']
        
        When inheriting from BaseErrorRate, 
            - method .__call__() must be defined and should end
              by a call to .compute() method
            - method .pretty() should be overridden
        """
        super(BaseErrorRate, self).__init__()
        
        self.__name = name
        self.__numerator = dict(numerator)
        self.__denominator = dict(denominator)
        if other:
            self.__other = list(other)
        else:
            self.__other = []
        
        self.__details = self.initialize()

    def __get_name(self): 
        return self.__name
    name = property(fget=__get_name, \
                     fset=None, \
                     fdel=None, \
                     doc="Metric name.")

    def initialize(self):
        detail = dict()
        detail.update( {name:0 for name in self.__numerator })
        detail.update( {name:0 for name in self.__denominator })
        detail.update( {name:0 for name in self.__other })
        return detail

    def __get_details(self): 
        return self.compute(self.__details, accumulate=False, detailed=True)
    details = property(fget=__get_details, \
                     fset=None, \
                     fdel=None, \
                     doc="Global details.")

    def __accumulate(self, detail):
        
        for name, value in detail.iteritems():
            self.__details[name] += value

    def compute(self, detail, accumulate=True, detailed=False):
        
        if accumulate:
            self.__accumulate(detail)
        
        numerator = 0
        for name, coefficient in self.__numerator.iteritems():
            numerator += coefficient * detail[name]
        
        denominator = 0
        for name, coefficient in self.__denominator.iteritems():
            denominator += coefficient * detail[name]
        
        if denominator > 0:
            rate = 1. * numerator / denominator
        else:
            if numerator > 0:
                raise ValueError('Denominator is zero and numerator is not. What should I do?')
            else:
                rate = 0.
        
        if detailed:
            detail = dict(detail)
            detail.update({self.__name: rate})
            return detail
        else:
            return rate
    
    def pretty(self, detail):
        string = ""
        for name, value in detail.iteritems():
            string += "  - %s: %g\n" % (name, value)
        return string
    
    def __str__(self):
        return self.pretty(self.details)
    
    def __abs__(self):
        return self.compute(self.__details, accumulate=False, detailed=False)    
