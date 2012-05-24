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


class BaseAgglomerativeClustering(object):
    """
    Base class for agglomerative clustering algorithms.
    
    """
    def __init__(self):
        super(BaseAgglomerativeClustering, self).__init__()
    
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
    
    # == Models ==
    
    def _compute_model(self, label):
        """
        Compute model for a given `label`
        
        Parameters
        ----------
        label : valid Annotation label
        
        Returns
        -------
        model : anything
            Any object that can serve as a model for `label` (if needed)
        
        """
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_compute_model()' % name)
    
    def _merge_models(self, merged_labels):
        """
        Compute new merged model
        
        Parameters
        ----------
        merged_labels : list
            List of merged labels
            
        Returns
        -------
        model : anything
            Any object that can serve as a model for the merged labels.
        
        """
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_merge_models()' % name)
    
    # ==
    
    def _initialize(self):
        """
        Initialize algorithm internals.
        """
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_initialize()' % name)
    
    def _next(self):
        """
        Next agglomerative clustering iteration.
        
        Returns
        -------
        labels : list
            List of `labels` that should be merged.
        
        """
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_next()' % name)
    
    def _update(self, new_label, merged_labels):
        """
        Update algorithm internals after merging.
        
        new_label <-- merged_labels
        
        
        
        Parameters
        ----------
        new_label : valid Annotation label
        
        merged_labels : list of valid Annotation labels
        
        
        """
        name = self.__class.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_update()' % name)
    
    def _stop(self, value):
        """
        Stopping criterion
        
        Returns
        -------
        stop : bool
            True if stopping criterion is met, False otherwise
            
        """
        return False
    
    def _final(self, annotation):
        """By default, current version is returned"""
        return self.__annotation.copy()
    
    # == Constraints ==
    
    def _initialize_constraint(self, **kwargs):
        """By default, there is no constraint whatsoever"""
        pass
        
    def _update_constraint(self, new_label, merged_labels):
        """By default, there is no constraint whatsoever"""
        pass
        
    def _mergeable(self, labels):
        """By default, there is no constraint whatsoever.
           Any set of labels are mergeable.
        """
        return True
    
    def __call__(self, annotation, feature, **kwargs):
        
        # initial annotation (will be modified)
        self.__annotation = annotation.copy()
        # initial feature (should stay untouched)
        self.__feature = feature
        
        # one model per label
        self.__models = {}
        for label in self.annotation.labels():
            self.__models[label] = self._compute_model(label)
        
        # initialize constraint if needed
        self._initialize_constraint(**kwargs)
        
        # initialize what needs to be initialized
        self._initialize()
        
        # keep track of iterations
        self.__iterations = []
        
        while True:
            
            # find labels that should be merged next
            merged_labels, status = self._next()
            
            # nothing left to merge or reached stopping criterion?
            if not merged_labels or self._stop(status):
                break
            
            # merge models
            new_label = merged_labels[0]
            self.__models[new_label] = self._merge_models(merged_labels)
            
            # remove old models
            old_labels = merged_labels[1:]
            for old_label in old_labels:
                del self.__models[old_label]
            
            # update internal annotation
            translation = {old_label : new_label for old_label in old_labels}
            self.__annotation = self.__annotation % translation
            
            # update constraint if needed
            self._update_constraint(new_label, merged_labels)
            
            # update what needs to be updated
            self._update(new_label, merged_labels)
            
            # keep track of iteration
            self.__iterations.append((new_label, merged_labels, status))
        
        return self._final(annotation)


import numpy as np
from pyannote.base.matrix import LabelMatrix
class MatrixAgglomerativeClustering(BaseAgglomerativeClustering):
    """
    Agglomerative clustering based on label similarity matrix.
    """
    def __get_matrix(self):
        return self.__matrix
    matrix = property(fget=__get_matrix)
    """Similarity matrix."""
    
    def _compute_similarity(self, label, other_label):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_compute_similarity()' % name)
        
    def _initialize(self):
        """
        Loop on all pairs of labels and fill similarity matrix
        """
        # initialize empty similarity matrix
        self.__matrix = LabelMatrix(default=-np.inf)
        
        # compute symmetric similarity matrix
        labels = self.annotation.labels()
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                similarity = self._compute_similarity(label, other_label)
                self.__matrix[label, other_label] = similarity
                self.__matrix[other_label, label] = similarity
    
    def _update(self, new_label, merged_labels):
        """
        Update similarity matrix for newly created label
        """
        
        # remove rows and columns for old labels
        for label in merged_labels:
            if label == new_label:
                continue
            del self.__matrix[label, :]
            del self.__matrix[:, label]
        
        # update row and column for new label
        labels = self.annotation.labels()
        for label in labels:
            if label == new_label:
                continue
            similarity = self._compute_similarity(new_label, label)
            self.__matrix[new_label, label] = similarity
            self.__matrix[label, new_label] = similarity
    
    def _next(self):
        
        while True:
            
            # find two most similar labels
            label1, label2 = self.__matrix.argmax().popitem()
            
            # if even the most similar labels are completely dissimilar
            # return empty list
            if self.__matrix[label1, label2] == -np.inf:
                return [], -np.inf
            
            # if labels are mergeable
            if self._mergeable([label1, label2]):
                similarity = self.__matrix[label1, label2]
                return sorted([label1, label2]), similarity
            
            # if labels are not mergeable, loop...
            # (and make sure those two are not selected again)
            else:
                self.__matrix[label1, label2] = -np.inf
                self.__matrix[label2, label1] = -np.inf


import networkx as nx
class GraphAgglomerativeClustering(MatrixAgglomerativeClustering):
    
    def __get_graph(self):
        return self.__graph
    graph = property(fget=__get_graph)
    """Similarity graph."""
    
    def _initialize(self):
        """
        One node per track, with 'label' attribute.
        Edge between two nodes is weighted
        """
        
        super(GraphAgglomerativeClustering, self)._initialize()
        
        # initialize empty graph
        self.__graph = nx.Graph()
        
        # add one node per label
        labels = self.annotation.labels()
        for label in labels:
            self.__graph.add_node(label, label=label)
        
        # add edges
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                similarity = max(0., self.matrix[label, other_label])
                self.__graph.add_edge(label, other_label, weight=similarity)
                
        # from matplotlib import pyplot as plt
        # plt.ion()
        # pos = nx.spring_layout(self.__graph)
        # nx.draw(self.__graph, pos)
        
        
    def _update(self, new_label, merged_labels):
        """
        Update similarity matrix for newly created label
        """
        
        super(GraphAgglomerativeClustering, self)._update(new_label,
                                                          merged_labels)
        
        # update node labels
        for label in merged_labels:
            self.__graph.node[label]['label'] = new_label
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()
