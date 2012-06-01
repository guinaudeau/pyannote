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

class BaseConstraintMixin(object):
    
    def cmx_setup(self, **kwargs):
        pass
    
    def cmx_init(self, **kwargs):
        pass
    
    def cmx_update(self, new_label, merged_labels):
        pass
    
    def cmx_meet(self, labels):
        return True

class BaseStoppingCriterionMixin(object):
    
    def smx_setup(self, **kwargs):
        pass
    
    def smx_stop(self, value):
        return False

class BaseModelMixin(object):
    
    def mmx_setup(self, **kwargs):
        pass
    
    def mmx_fit(self, label):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_fit()' % name)
    
    def mmx_compare(self, label, other_label):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_compare()' % name)
    
    def mmx_merge(self, labels):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_merge()' % name)

import networkx as nx
class BaseAgglomerativeClustering(object):
    """
    Base class for agglomerative clustering algorithms.
    
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
        super(BaseAgglomerativeClustering, self).__init__()
        
        # setup constraint mixins (CMx)
        self.CMx = self.getMx(BaseConstraintMixin)
        for cmx in self.CMx:
            cmx.cmx_setup(self, **kwargs)
        
        # setup every stopping criteria
        self.SMx = self.getMx(BaseStoppingCriterionMixin)
        for smx in self.SMx:
            smx.smx_setup(self, **kwargs)
        
        # setup model
        MMx = self.getMx(BaseModelMixin)
        if len(MMx) == 0:
            raise ValueError('Missing model mixin (MMx).')
        elif len(MMx) > 1:
            raise ValueError('Too many model mixins (MMx): %s' % MMx)
        self.MMx = MMx[0]
        self.MMx.mmx_setup(self, **kwargs)
        
        # setup internal
        IMx = self.getMx(BaseInternalMixin)
        if len(IMx) == 0:
            raise ValueError('Missing internal mixin (IMx).')
        elif len(IMx) > 1:
            raise ValueError('Too many internal mixins(IMx) : %s' % IMx)
        self.IMx = IMx[0]
        self.IMx.imx_setup(self, **kwargs)
        
    def __get_annotation(self):
        return self.__annotation
    annotation = property(fget=__get_annotation)
    """Current state of annotation"""
    
    def __get_feature(self):
        return self.__feature
    feature = property(fget=__get_feature)
    """Original feature"""
    
    def __get_models(self):
        return self.__models
    models = property(fget=__get_models)
    """One model per label"""
    
    def __get_iterations(self):
        return self.__iterations
    iterations = property(fget=__get_iterations)
    """Iterations log"""
    
    def fit(self, label):
        return self.MMx.mmx_fit(self, label)
    
    def init(self):
        self.IMx.imx_init(self)
    
    def next(self):
        return self.IMx.imx_next(self)
    
    def stop(self, status):
        for smx in self.SMx:
            if smx.smx_stop(self, status):
                return True
        return False
    
    def merge(self, merged_labels):
        return self.MMx.mmx_merge(self, merged_labels)
    
    def update(self, new_label, merged_labels):
        self.IMx.imx_update(self, new_label, merged_labels)
    
    def final(self, annotation):
        """By default, current version is returned"""
        return self.__annotation.copy()
    
    def meet_constraints(self, labels):
        for cmx in self.CMx:
            if not cmx.cmx_meet(self, labels):
                return False
        return True
    
    def __call__(self, annotation, feature, **kwargs):
        
        # initial annotation (will be modified)
        self.__annotation = annotation.copy()
        # initial feature (should stay untouched)
        self.__feature = feature
        
        # one model per label
        self.__models = {}
        for label in self.annotation.labels():
            self.__models[label] = self.fit(label)
        
        # initialize internals
        self.init()
        
        # initialize constraints
        for cmx in self.CMx:
            cmx.cmx_init(self, **kwargs)
        
        # keep track of iterations
        self.__iterations = []
        
        while True:
            
            # find labels that should be merged next
            merged_labels, status = self.next()
            
            # nothing left to merge or reached stopping criterion?
            if not merged_labels or self.stop(status):
                break
            
            # merge models
            new_label = merged_labels[0]
            self.__models[new_label] = self.merge(merged_labels)
            
            # remove old models
            old_labels = merged_labels[1:]
            for old_label in old_labels:
                del self.__models[old_label]
            
            # update internal annotation
            translation = {old_label : new_label for old_label in old_labels}
            self.__annotation = self.__annotation % translation
            
            # update what needs to be updated
            self.update(new_label, merged_labels)
            
            # update constraint if needed
            for cmx in self.CMx:
                cmx.cmx_update(self, new_label, merged_labels)
            
            # keep track of iteration
            self.__iterations.append((new_label, merged_labels, status))
        
        return self.final(annotation)

class BaseInternalMixin(object):
    
    def imx_setup(self, **kwargs):
        pass
    
    def imx_init(self):
        pass
    
    def imx_update(self, new_label, merged_labels):
        pass
    
    def imx_next(self):
        pass
        
    
import numpy as np
from pyannote.base.matrix import LabelMatrix

class MatrixIMx(BaseInternalMixin):
    
    def imx_init(self):
        """
        Loop on all pairs of labels and fill similarity matrix
        """
        
        # initialize empty similarity matrix
        self.imx_similarity = LabelMatrix(default=-np.inf)
        
        # compute symmetric similarity matrix
        labels = self.annotation.labels()
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                s = self.MMx.mmx_compare(self, label, other_label)
                self.imx_similarity[label, other_label] = s
                self.imx_similarity[other_label, label] = s
    
    def imx_update(self, new_label, merged_labels):
        """
        Update similarity matrix for newly created label
        """
        
        # remove rows and columns for old labels
        for label in merged_labels:
            if label == new_label:
                continue
            del self.imx_similarity[label, :]
            del self.imx_similarity[:, label]
        
        # update row and column for new label
        labels = self.annotation.labels()
        for label in labels:
            if label == new_label:
                continue
            s = self.MMx.mmx_compare(self, new_label, label)
            self.imx_similarity[new_label, label] = s
            self.imx_similarity[label, new_label] = s
    
    def imx_next(self):
        
        while True:
            
            # find two most similar labels
            label1, label2 = self.imx_similarity.argmax().popitem()
            
            # if even the most similar labels are completely dissimilar
            # return empty list
            if self.imx_similarity[label1, label2] == -np.inf:
                return [], -np.inf
                
            # if labels are mergeable
            if self.meet_constraints([label1, label2]):
                s = self.imx_similarity[label1, label2]
                return sorted([label1, label2]), s
            
            # if labels are not mergeable, loop...
            # (and make sure those two are not selected again)
            else:
                self.imx_similarity[label1, label2] = -np.inf
                self.imx_similarity[label2, label1] = -np.inf


if __name__ == "__main__":
    import doctest
    doctest.testmod()
