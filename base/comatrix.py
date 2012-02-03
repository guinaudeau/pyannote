#!/usr/bin/env python
# encoding: utf-8

import numpy as np

class CoMatrix(object):
    def __init__(self, ilabels, jlabels, Mij):
        super(CoMatrix, self).__init__()
        
        self.ilabels = ilabels
        self.jlabels = jlabels
        self.Mij = Mij
        
        self.label2i = {ilabel:i for i, ilabel in enumerate(ilabels)}
        self.label2j = {jlabel:i for i, jlabel in enumerate(jlabels)}
        
        
    def __get_T(self): 
        return CoMatrix(self.jlabels, self.ilabels, self.Mij.T)
    T = property(fget=__get_T, \
                     fset=None, \
                     fdel=None, \
                     doc="Matrix transposition.")
    
    def __getitem__(self, key):
        """
        """
        if isinstance(key, tuple) and len(key) == 2:
            
            ilabel = key[0]
            jlabel = key[1]
            
            if ilabel in self.label2i and jlabel in self.label2j:
                return self.Mij[self.label2i[ilabel], self.label2j[jlabel]]
        
        raise KeyError('')
    
    def __setitem__(self, key, value):
        raise NotImplementedError('')
    
    def __delitem__(self, key):
        raise NotImplementedError('')
    
    def __call__(self, ilabel):
        if ilabel in self.label2i:
            i = self.label2i[ilabel]
            return {jlabel: self.Mij[i, self.label2j[jlabel]] for jlabel in self.label2j}
        else:
            return {}
            
class Confusion(CoMatrix):
    """
    Confusion matrix between two (ID-based) annotations
    
    :param I: first (ID-based) annotation
    :type I: :class:`TrackIDAnnotation`

    :param J: second (ID-based) annotation
    :type J: :class:`TrackIDAnnotation`
    
    >>> M = Confusion(A, B)

    Get total confusion duration (in seconds) between id_A and id_B::
    
    >>> confusion = M[id_A, id_B]
    
    Get confusion dictionary for id_A::
    
    >>> confusions = M(id_A)
    
    
    """
    def __init__(self, I, J):
                
        n_i = len(I.IDs)
        n_j = len(J.IDs)
        Mij = np.zeros((n_i, n_j))
        super(Confusion, self).__init__(I.IDs, J.IDs, Mij)
        
        for ilabel in self.label2i:
            i = self.label2i[ilabel]
            i_coverage = I(ilabel).timeline.coverage()
            for jlabel in self.label2j:
                j = self.label2j[jlabel]
                j_coverage = J(jlabel).timeline.coverage()
                
                self.Mij[i, j] = i_coverage(j_coverage, mode='intersection').duration()
        
        
        
        
        
        
        
        