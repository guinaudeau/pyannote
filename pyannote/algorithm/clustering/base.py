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
    
    def _setup_constraint(self, **kwargs):
        pass
    
    def _initialize_constraint(self, **kwargs):
        pass
    
    def _update_constraint(self, new_label, merged_labels):
        pass
    
    def _meet_constraint(self, labels):
        return True

class BaseStoppingCriterionMixin(object):
    
    def _setup_stop(self, **kwargs):
        pass
    
    def _stop(self, value):
        return False

class BaseModelMixin(object):
    
    def _setup_model(self, **kwargs):
        pass
    
    def _compute_model(self, label):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_compute_model()' % name)
    
    def _model_similarity(self, label, other_label):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_model_similarity()' % name)
    
    def _merge_models(self, labels):
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  '_merge_models()' % name)

class BaseAgglomerativeClustering(object):
    """
    Base class for agglomerative clustering algorithms.
    
    """
    
    def getMixins(self, baseMixin):
        cls = self.__class__
        return [mixin for mixin in cls.mro() 
                      if issubclass(mixin, baseMixin) and
                         mixin != cls and mixin != baseMixin]
    
    def __init__(self, **kwargs):
        super(BaseAgglomerativeClustering, self).__init__()
        
        # setup every constraints
        self._constraintMixins = self.getMixins(BaseConstraintMixin)
        for constraintMixin in self._constraintMixins:
            constraintMixin._setup_constraint(self, **kwargs)
        
        # setup every stopping criteria
        self._stopMixins = self.getMixins(BaseStoppingCriterionMixin)
        for stopMixin in self._stopMixins:
            stopMixin._setup_stop(self, **kwargs)
        
        # setup models
        self._modelMixin = self.getMixins(BaseModelMixin)[-1]
        self._modelMixin._setup_model(self, **kwargs)
        
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
    
    # def _compute_model(self, label):
    #     """
    #     Compute model for a given `label`
    #     
    #     Parameters
    #     ----------
    #     label : valid Annotation label
    #     
    #     Returns
    #     -------
    #     model : anything
    #         Any object that can serve as a model for `label` (if needed)
    #     
    #     """
    #     return None
    # 
    # def _merge_models(self, merged_labels):
    #     """
    #     Compute new merged model
    #     
    #     Parameters
    #     ----------
    #     merged_labels : list
    #         List of merged labels
    #         
    #     Returns
    #     -------
    #     model : anything
    #         Any object that can serve as a model for the merged labels.
    #     
    #     """
    #     return None
    # ==
    
    # def _initialize(self):
    #     """
    #     Initialize algorithm internals.
    #     """
    #     pass
    # 
    # def _next(self):
    #     """
    #     Next agglomerative clustering iteration.
    #     
    #     Returns
    #     -------
    #     labels : list
    #         List of `labels` that should be merged.
    #     
    #     """
    #     return []
    
    # def _update(self, new_label, merged_labels):
    #     """
    #     Update algorithm internals after merging.
    #     
    #     new_label <-- merged_labels
    #     
    #     
    #     
    #     Parameters
    #     ----------
    #     new_label : valid Annotation label
    #     
    #     merged_labels : list of valid Annotation labels
    #     
    #     
    #     """
    #     pass
    
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
    
    def _initialize_constraints(self, **kwargs):
        for constraintMixin in self._constraintMixins:
            constraintMixin._initialize_constraint(self, **kwargs)
        
    def _update_constraints(self, new_label, merged_labels):
        for constraintMixin in self._constraintMixins:
            constraintMixin._update_constraint(self, new_label, merged_labels)
        
    def _meet_constraints(self, labels):
        for constraintMixin in self._constraintMixins:
            if not constraintMixin._meet_constraint(self, labels):
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
            self.__models[label] = self._compute_model(label)
        
        # initialize what needs to be initialized
        self._initialize()
        
        # initialize constraints if needed
        self._initialize_constraints(**kwargs)
        
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
            
            # update what needs to be updated
            self._update(new_label, merged_labels)
            
            # update constraint if needed
            self._update_constraints(new_label, merged_labels)
            
            # keep track of iteration
            self.__iterations.append((new_label, merged_labels, status))
        
        return self._final(annotation)

class BaseIterationMixin(object):
    
    def _initialize(self):
        pass
    
    def _update(self, new_label, merged_labels):
        pass
    
    def _next(self):
        pass

import numpy as np
from pyannote.base.matrix import LabelMatrix

class MatrixMixin(BaseIterationMixin):
    
    def _get_similarity(self):
        return self._similarity
    similarity = property(fget=_get_similarity)
    
    def _initialize(self):
        """
        Loop on all pairs of labels and fill similarity matrix
        """
        
        # initialize empty similarity matrix
        self._similarity = LabelMatrix(default=-np.inf)
        
        # compute symmetric similarity matrix
        labels = self.annotation.labels()
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                s = self._model_similarity(label, other_label)
                self._similarity[label, other_label] = s
                self._similarity[other_label, label] = s
    
    def _update(self, new_label, merged_labels):
        """
        Update similarity matrix for newly created label
        """
        
        # remove rows and columns for old labels
        for label in merged_labels:
            if label == new_label:
                continue
            del self._similarity[label, :]
            del self._similarity[:, label]
        
        # update row and column for new label
        labels = self.annotation.labels()
        for label in labels:
            if label == new_label:
                continue
            s = self._model_similarity(new_label, label)
            self._similarity[new_label, label] = s
            self._similarity[label, new_label] = s
    
    def _next(self):
        
        while True:
            
            # find two most similar labels
            label1, label2 = self._similarity.argmax().popitem()
            
            # if even the most similar labels are completely dissimilar
            # return empty list
            if self._similarity[label1, label2] == -np.inf:
                return [], -np.inf
                
            # if labels are mergeable
            if self._meet_constraints([label1, label2]):
                s = self._similarity[label1, label2]
                return sorted([label1, label2]), s
            
            # if labels are not mergeable, loop...
            # (and make sure those two are not selected again)
            else:
                self._similarity[label1, label2] = -np.inf
                self._similarity[label2, label1] = -np.inf


if __name__ == "__main__":
    import doctest
    doctest.testmod()
