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

from pyannote.algorithm.clustering.similarity import BaseSimilarityMixin
from pyannote.algorithm.util.gaussian import Gaussian
class BICSimilarityMixin(BaseSimilarityMixin):
    
    def __get_penalty_coef(self):
        return self.__penalty_coef
    def __set_penalty_coef(self, value):
        self.__penalty_coef = float(value)
    penalty_coef = property(fget=__get_penalty_coef, fset=__set_penalty_coef)
    """Coefficient of model size penalty."""
    
    def __get_covariance_type(self):
        return self.__covariance_type
    def __set_covariance_type(self, value):
        self.__covariance_type = str(value)
    covariance_type = property(fget=__get_covariance_type,
                               fset=__set_covariance_type)
    """Type of covariance matrix."""
    
    def _compute_model(self, label):
        """
        One Gaussian per track
        """
        # extract features for this label
        data = self.feature(self.annotation.label_timeline(label))
        # fit gaussian and return it
        return Gaussian(covariance_type=self.covariance_type).fit(data)
    
    def _compute_similarity(self, label, other_label):
        """
        Delta BIC between two Gaussians
        """
        model = self.models[label]
        other_model = self.models[other_label]
        dissimilarity, _ = model.bic(other_model,
                                     penalty_coef=self.penalty_coef)
        return (-dissimilarity)
    
    def _merge_models(self, labels):
        """
        Fast merge of two Gaussians
        """
        new_model = self.models[labels[0]]
        for label in labels[1:]:
            new_model = new_model.merge(self.models[label])
        return new_model

from pyannote.algorithm.clustering.base import MatrixAgglomerativeClustering
from pyannote.algorithm.clustering.stop import NegativeStoppingCriterionMixin
class BICClustering(NegativeStoppingCriterionMixin, BICSimilarityMixin, \
                    MatrixAgglomerativeClustering):
    """
    BIC clustering 
    
    Parameters
    ----------
    covariance_type : {'full', 'diag'}, optional
        Full or diagonal covariance matrix. Default is 'full'.
    penalty_coef : float, optional
        Coefficient of model size penalty. Default is 3.5.
        
    Examples
    --------
        
        >>> clustering = BICClustering()
        >>> annotation = Annotation(...)
        >>> feature = PrecomputedPeriodicFeature( ... )
        >>> new_annotation = clustering(annotation, feature)
        
    """
    
    def __init__(self, covariance_type='full', penalty_coef=3.5):
        super(BICClustering, self).__init__()
        self.penalty_coef = penalty_coef
        self.covariance_type = covariance_type

from pyannote.algorithm.clustering.constraint import ContiguousConstraintMixin
class BICRecombiner(ContiguousConstraintMixin, BICClustering):
    """
    Recombine contiguous segments based on BIC criterion.
    
    Parameters
    ----------
    covariance_type : {'full', 'diag'}, optional
        Full or diagonal covariance matrix. Default is 'diag'.
    penalty_coef : float, optional
        Coefficient for model size penalty. Default is 3.5.
    tolerance : float, optional
        Temporal tolerance for notion of 'contiguous' segments, in seconds.
        Default is 500ms.
        
    Examples
    --------
        
        >>> clustering = BICClustering()
        >>> annotation = Annotation(...)
        >>> feature = PrecomputedPeriodicFeature( ... )
        >>> new_annotation = clustering(annotation, feature)
    
    """
    def __init__(self, covariance_type='diag', penalty_coef=3.5, tolerance=0.5):
        super(BICRecombiner, self).__init__(covariance_type=covariance_type, 
                                            penalty_coef=penalty_coef)
        self.tolerance = tolerance


from pyannote.algorithm.clustering.base import GraphAgglomerativeClustering
from pyannote.algorithm.util.community import modularity
import numpy as np
class BICClusteringModularity(BICSimilarityMixin, GraphAgglomerativeClustering):
    
    def __init__(self, covariance_type='full', penalty_coef=3.5):
        super(BICClusteringModularity, self).__init__()
        self.penalty_coef = penalty_coef
        self.covariance_type = covariance_type
    
    def _next(self):
        merged_labels, similarity = super(GraphAgglomerativeClustering,
                                          self)._next()
        partition = {node: data['label'] 
                     for node, data in self.graph.nodes_iter(data=True)}
        return merged_labels, modularity(partition, self.graph)
    
    def _final(self, annotation):
        final = annotation.copy()
        imax = np.argmax([v for l, L, v in self.iterations])
        for new_label, old_labels, value in self.iterations[:imax+1]:
            translation = {label : new_label for label in old_labels}
            final = final % translation
        return final


if __name__ == "__main__":
    import doctest
    doctest.testmod()
  