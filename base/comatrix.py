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
    
    def __get_shape(self):
        return self.Mij.shape
    shape = property(fget=__get_shape, \
                     fset=None, \
                     fdel=None, \
                     doc="Matrix shape.")
                     
    def __get_M(self):
        return self.Mij
    M = property(fget=__get_M, \
                 fset=None, \
                 fdel=None, \
                 doc="numpy matrix.")
                 
    def __get_labels(self):
        return self.ilabels, self.jlabels
    labels = property(fget=__get_labels, \
                      fset=None, \
                      fdel=None,
                      doc="Matrix labels.")
    
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
            return {jlabel: self.Mij[i, self.label2j[jlabel]] \
                    for jlabel in self.label2j}
        else:
            return {}
            
    def argmin(self, threshold=None):
        """
        :param threshold: threshold on minimum value
        :type threshold: float
        
        :returns: list of label pairs corresponding to minimum value in matrix.
        In case :data:`threshold` is provided and is smaller than minimum value,
        then, returns an empty list.
        """
        m = np.min(self.M)
        if (threshold is None) or (m < threshold):
            pairs = np.argwhere(self.M == m)
        else:
            pairs = []
        return [(self.ilabels[i], self.jlabels[j]) for i, j in pairs]

    def argmax(self, threshold=None):
        """
        :param threshold: threshold on maximum value
        :type threshold: float
        
        :returns: list of label pairs corresponding to maximum value in matrix.
        In case :data:`threshold` is provided and is higher than maximum value,
        then, returns an empty list.
        """
        M = np.max(self.M)
        if (threshold is None) or (M > threshold):
            pairs = np.argwhere(self.M == M)
        else:
            pairs = []
        return [(self.ilabels[i], self.jlabels[j]) for i, j in pairs]
        
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
    def __init__(self, I, J, normalize=False):
                
        n_i = len(I.IDs)
        n_j = len(J.IDs)
        Mij = np.zeros((n_i, n_j))
        super(Confusion, self).__init__(I.IDs, J.IDs, Mij)
        
        if normalize:
            iduration = np.zeros((n_i,))
            
        for ilabel in self.label2i:
            i = self.label2i[ilabel]
            i_coverage = I(ilabel).timeline.coverage()
            if normalize:
                iduration[i] = i_coverage.duration()
            
            for jlabel in self.label2j:
                j = self.label2j[jlabel]
                j_coverage = J(jlabel).timeline.coverage()
                self.Mij[i, j] = i_coverage(j_coverage, mode='intersection').duration()
        
        if normalize:
            for i in range(n_i):
                self.Mij[i, :] = self.Mij[i, :] / iduration[i]

class AutoConfusion(Confusion):
    """
    Auto confusion matrix 
    
    :param I: (ID-based) annotation
    :type I: :class:`TrackIDAnnotation`

    :param neighborhood:
    :type neighborhood: 
    
    >>> M = AutoConfusion(A, neighborhood=10)

    Get total confusion duration (in seconds) between id_A and id_B::
    
    >>> confusion = M[id_A, id_B]
    
    Get confusion dictionary for id_A::
    
    >>> confusions = M(id_A)
    
    
    """
    def __init__(self, I, neighborhood=0., normalize=False):
        
        map_func = lambda segment : neighborhood << segment >> neighborhood
        
        xI = I.toTrackIDAnnotation().copy(map_func=map_func)        
        super(AutoConfusion, self).__init__(xI, xI, normalize=normalize)
            
        
