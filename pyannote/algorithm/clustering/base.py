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
    
    def _compute_model(self, label):
        raise NotImplementedError('')
    
    def _initialize(self):
        raise NotImplementedError('')
        
    def _next(self):
        raise NotImplementedError('')
        
    def _merge_models(self, labels):
        raise NotImplementedError('')
    
    def _update(self, new_label, old_labels):
        raise NotImplementedError('')
    
    def __call__(self, annotation, feature):
        
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
        
        while True:
            
            # find labels that should be merged next
            labels = self._next()
            
            # nothing to merge? stop.
            if not labels:
                break
            
            # merge models
            new_label = labels[0]
            self.__models[new_label] = self._merge_models(labels)
            
            # remove old models
            old_labels = labels[1:]
            for old_label in old_labels:
                del self.__models[old_label]
            
            # update internal annotation
            translation = {old_label : new_label for old_label in old_labels}
            self.__annotation = self.__annotation % translation
            
            # update what needs to be updated
            self._update(new_label, old_labels)
        
        return self.__annotation.copy()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
