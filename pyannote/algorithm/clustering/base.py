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


class BaseInternalMixin(object):
    
    def imx_setup(self, **kwargs):
        pass
    
    def imx_init(self):
        pass
    
    def imx_update(self, new_label, merged_labels):
        pass
    
    def imx_do_not_merge(self, labels):
        raise NotImplementedError('')
    
    def imx_next(self):
        raise NotImplementedError('')

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
            # this is to ensure the order of labels in row & column
            self.imx_similarity[label, label] = self.imx_similarity.default
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
    
    def imx_do_not_merge(self, labels):
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                self.imx_similarity[label, other_label] = -np.inf
                self.imx_similarity[other_label, label] = -np.inf
    
    def imx_next(self):
        
        # find two most similar labels
        label1, label2 = self.imx_similarity.argmax().popitem()
        s = self.imx_similarity[label1, label2]
        
        # if they are completely dissimilar, do not merge
        if s == -np.inf:
            return [], -np.inf
        
        return [label1, label2], s



import networkx as nx
from pyannote.algorithm.clustering.mmx.base import BaseModelMixin
from pyannote.algorithm.clustering.cmx.base import BaseConstraintMixin
from pyannote.algorithm.clustering.smx.base import BaseStoppingCriterionMixin

class AgglomerativeClustering(object):
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
        super(AgglomerativeClustering, self).__init__()
        
        # setup constraint mixins (CMx)
        self.CMx = self.getMx(BaseConstraintMixin)
        for cmx in self.CMx:
            cmx.cmx_setup(self, **kwargs)
        
        # setup stopping criteria
        SMx = self.getMx(BaseStoppingCriterionMixin)
        if len(SMx) == 0:
            SMx = [BaseStoppingCriterionMixin]
        elif len(SMx) > 1:
            raise ValueError('Too many stopping criteria (SMx): %s' % SMx )
        self.SMx = SMx[0]
        self.SMx.smx_setup(self, **kwargs)
        
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
    
    
    # --- INTERNALS IMx ---
    
    def init_internals(self):
        self.IMx.imx_init(self)
    
    def update_internals(self, new_label, merged_labels):
        self.IMx.imx_update(self, new_label, merged_labels)
    
    def next(self):
        return self.IMx.imx_next(self)
    
    def do_not_merge(self, labels):
        self.IMx.imx_do_not_merge(self, labels)
    
    # --- MODELS MMx ---
    
    def init_models(self):
        self.__models = {L: self.MMx.mmx_fit(self, L) 
                        for L in self.annotation.labels()}
    
    def merge_models(self, merged_labels):
        new_label = merged_labels[0]
        self.__models[new_label] = self.MMx.mmx_merge(self, merged_labels)
        old_labels = merged_labels[1:]
        for old_label in old_labels:
            del self.__models[old_label]
        return new_label, old_labels
    
    # --- CONSTRAINTS CMx ---
    
    def init_constraints(self, **kwargs):
        for cmx in self.CMx:
            cmx.cmx_init(self, **kwargs)
    
    def update_constraints(self, new_label, merged_labels):
        for cmx in self.CMx:
            cmx.cmx_update(self, new_label, merged_labels)
    
    def meet_constraints(self, labels):
        for cmx in self.CMx:
            if not cmx.cmx_meet(self, labels):
                return False
        return True
    
    # --- STOPPING CRITERION SMx ---
    
    def init_stopping_criterion(self):
        self.SMx.smx_init(self)
    
    def update_stopping_criterion(self, new_label, merged_labels):
        self.SMx.smx_update(self, new_label, merged_labels)
    
    def stop(self, status):
        return self.SMx.smx_stop(self, status)
    
    def final(self, annotation):
        return self.SMx.smx_final(self, annotation)
    
    def __call__(self, annotation, feature, **kwargs):
        
        self.__annotation = annotation.copy()
        self.__feature = feature
        self.__iterations = []
        
        # initialize models
        self.init_models()
        
        # initialize internals
        self.init_internals()
        
        # initialize constraints
        self.init_constraints(**kwargs)
        
        # initialize stopping criterion
        self.init_stopping_criterion()
        
        while True:
            
            # find labels that should (and can) be merged next
            while True:
                
                # find labels that should be merged
                merged_labels, status = self.next()
                
                # are there any? if not, stop looking.
                if not merged_labels:
                    break
                
                # are they mergeable?
                if self.meet_constraints(merged_labels):
                    break
                
                # if they are not,
                # make sure we do not try to merge them again
                self.do_not_merge(merged_labels)
            
            # nothing left to merge or reached stopping criterion?
            if not merged_labels or self.stop(status):
                break
            
            # merge models
            new_label, old_labels = self.merge_models(merged_labels)
            
            # update internal annotation
            translation = {old_label : new_label for old_label in old_labels}
            self.__annotation = self.__annotation % translation
            
            # update what needs to be updated
            self.update_internals(new_label, merged_labels)
            
            # update constraint if needed
            self.update_constraints(new_label, merged_labels)
            
            # update stopping criterion if needed
            self.update_stopping_criterion(new_label, merged_labels)
            
            # keep track of this iteration
            self.__iterations.append((new_label, merged_labels, status))
        
        return self.final(annotation)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
