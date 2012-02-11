#!/usr/bin/env python
# encoding: utf-8

class NoMatch(object):
    nextID = 0
    
    @classmethod
    def reset(cls):
        cls.nextID = 0
    
    def __init__(self, format='NoMatch%03d'):
        super(NoMatch, self).__init__()
        self.ID = NoMatch.nextID
        self.format = format
        NoMatch.nextID += 1
    
    def __str__(self):
        return self.format % self.ID
    
    def __repr__(self):
        return str(self)


class ULabel(object):
    """docstring for Label"""
    def __init__(self, u, label):
        super(ULabel, self).__init__()
        self.u = u
        self.label = label
        
    def __eq__(self, other):
        return (self.u == other.u) & \
               (self.label  == other.label)
    
    def __hash__(self):
        return hash(self.label)
        
