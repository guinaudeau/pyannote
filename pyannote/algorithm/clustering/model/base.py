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

class BaseModelMixin(object):
    """
    Clustering model mixin
    
    """
    def mmx_setup(self, **kwargs):
        """
        Setup model internal variables
        """
        pass
    
    def mmx_fit(self, label, **kwargs):
        """
        Create model
        
        Parameters
        ----------
        label : any valid label
            The `label` to model
        
        Returns
        -------
        model : any object
            The model for `label`
        
        """
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_fit()' % name)
    
    def mmx_symmetric(self):
        """
        Is model similarity symmetric?
        
        Returns
        -------
        symmetric: bool
            True if similarity is symmetric, False otherwise.
        
        """
        return False
    
    def mmx_compare(self, label, other_label, **kwargs):
        """
        Similarity between two labels
        
        Parameters
        ----------
        label, other_label : any valid label
            The labels to compare
            
        Returns
        -------
        similarity : float
            Similarity between the two labels, the higher the more similar
        
        """
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_compare()' % name)
    
    def mmx_similarity_matrix(self, labels, **kwargs):
        """
        Compute label similarity matrix
        
        Parameters
        ----------
        labels : list of labels
        
        Returns
        -------
        X : array (num_labels, num_labels)
            Label similarity matrix
        
        """
        
        # number of labels
        N = len(labels)
        
        # one model per label
        models = {label: self.mmx_fit(label, **kwargs) for label in labels}
        
        # label similarity matrix
        X = np.empty((N, N))
        
        # loop on all pairs of labels
        for i, label in enumerate(labels):
            for j, other_label in enumerate(labels):
                
                # if similarity is symmetric, no need to compute Xji
                if self.mmx_symmetric() and j > i:
                    break
                
                # compute Xij
                X[i, j] = self.mmx_compare(label, other_label, 
                                           models=models, **kwargs)
                
                # if similarity is symmetric, propagate Xij to Xji
                if self.mmx_symmetric():
                    X[j, i] = X[i, j]
        
        # return label similarity matrix
        return X
    
    
    def mmx_merge(self, labels, **kwargs):
        """
        Merge models
        
        Parameters
        ----------
        labels : list of valid labels
            The labels whose models should be merged
            
        Returns
        -------
        model : any object
            The merged models
        
        """
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_merge()' % name)


class PrecomputedMMx(BaseModelMixin):
    
    def mmx_setup(self, precomputed=None, **kwargs):
        self.mmx_precomputed = precomputed
    
    def mmx_fit(self, label, **kwargs):
        return tuple([label])
    
    def mmx_merge(self, labels, models=None, **kwargs):
        
        if models is None:
            models = self.models
        
        new_model = []
        for label in labels:
            other_model = self.models[label]
            new_model.extend(other_model)
        return tuple(new_model)

class AverageLinkMMx(PrecomputedMMx):
    
    def mmx_compare(self, label, other_label, models=None, **kwargs):
        
        if models is None:
            models = self.models
        
        model = models[label]
        other_model = models[other_label]
        return np.mean(self.mmx_precomputed[set(model), set(other_model)].M)

class SingleLinkMMx(PrecomputedMMx):
    
    def mmx_compare(self, label, other_label, models=None, **kwargs):
        
        if models is None:
            models = self.models
        
        model = models[label]
        other_model = models[other_label]
        return np.max(self.mmx_precomputed[set(model), set(other_model)].M)

class CompleteLinkMMx(PrecomputedMMx):
    
    def mmx_compare(self, label, other_label, models=None, **kwargs):
        
        if models is None:
            models = self.models
        
        model = models[label]
        other_model = models[other_label]
        return np.min(self.mmx_precomputed[set(model), set(other_model)].M)



import networkx as nx
from pyannote.base.matrix import LabelMatrix

class SimilarityMatrix(object):
    """Helper class for label similarity matrix generation
    
    Just add a model mixin to it...
    
    """
    
    def getMx(self, baseMx):
        
        # get all mixins subclass of baseMx
        # but the class itself and the baseMx itself
        cls = self.__class__
        MX =  [Mx for Mx in cls.mro() 
                  if issubclass(Mx, baseMx) and Mx != cls and Mx != baseMx]
        
        # build the class inheritance directed graph {subclass --> class}
        G = nx.DiGraph()
        for m, Mx in enumerate(MX):
            G.add_node(Mx)
            for otherMx in MX[m+1:]:
                if issubclass(Mx, otherMx):
                    G.add_edge(Mx, otherMx)
                elif issubclass(otherMx, Mx):
                    G.add_edge(otherMx, Mx)
        
        # only keep the deeper subclasses in each component
        MX = []
        for components in nx.connected_components(G.to_undirected()):
            g = G.subgraph(components)
            MX.extend([Mx for Mx, degree in g.in_degree_iter() if degree == 0])
        
        return MX
    
    def __init__(self, **kwargs):
        super(SimilarityMatrix, self).__init__()
        
        # setup model
        MMx = self.getMx(BaseModelMixin)
        if len(MMx) == 0:
            raise ValueError('Missing model mixin (MMx).')
        elif len(MMx) > 1:
            raise ValueError('Too many model mixins (MMx): %s' % MMx)
        self.mmx_setup(**kwargs)
    
    def __call__(self, hypothesis, feature):
        """
        Compute label similarity matrix
        
        Parameters
        ----------
        hypothesis : Annotation
        
        feature : Feature
        
        Returns
        -------
        matrix : LabelMatrix
            Label similarity matrix, indexed with hypothesis labels.
        
        """
        labels = hypothesis.labels()
        M = self.mmx_similarity_matrix(labels, annotation=hypothesis,
                                       feature=feature)
        return LabelMatrix(ilabels=labels, jlabels=labels, Mij=M)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
