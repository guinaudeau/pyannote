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


import networkx as nx
from pyannote.base.matrix import LabelMatrix

class BaseLabelSimilarityMatrixGenerator(object):
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
        super(BaseLabelSimilarityMatrixGenerator, self).__init__()
        
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
        


# import pyfusion.normalization.bayes
# import numpy as np
# from pyannote.algorithm.mapping import ConservativeDirectMapper
# import networkx as nx
# class PosteriorMixin(object):
#     
#     def _get_X(self, annotation, feature):
#         """
#         Get label similarity matrix
#         
#         Parameters
#         ----------
#         annotation : :class:`Annotation`
#             Annotation for a given resource
#             (e.g. an intermediate segmentation with one label per segment)
#         feature : :class:`Feature`
#             Features extracted from the resource described by `annotation`
#         
#         Returns
#         -------
#         matrix : (N, N) array-like
#             Similarity matrix between `annotation` labels.
#             (follows order provided by `annotation.labels()`)
#         
#         """
#         
#         # similarity between labels
#         X = self.mmx_similarity_matrix(annotation.labels(),
#                                        annotation=annotation,
#                                        feature=feature)
#         return X
#     
#     def _get_y(self, input_annotation, output_annotation):
#         """
#         
#         Parameters
#         ----------
#         input_annotation : :class:`Annotation`
#             Input of clustering algorithm
#         output_annotation : :class:`Annotation`
#             Groundtruth annotation
#         """
#         
#         # Maps input label I to output label O
#         # if and only if O is the only one cooccurring with I
#         mapper = ConservativeDirectMapper()
#         mapping = mapper(input_annotation, output_annotation)
#         
#         labels = input_annotation.labels()
#         N = len(labels)
#         label2i = {label:i for i, label in enumerate(labels)}
#         
#         # Initialize y with -1
#         # ... meaning that 
#         y = -np.ones((N, N), dtype=np.int8)
#         
#         # This graph will help us determine which labels should be 
#         # in the same cluster, which labels should be in 2 different
#         # clusters, and which label we don't know nothing about
#         g = nx.Graph()
#         for ilabels, olabel in mapping:
#             # The graph only contains labels for which
#             # we could find a "conservative" mapping
#             # We can't tell anything about "being in the same cluster"
#             # for those labels with no match.
#             if not olabel or not ilabels:
#                 continue
#             # Create one node per label for which 
#             # a "conservative" mapping is found
#             # Add an edge between labels with the same mapping
#             ilabels = list(ilabels)
#             label = ilabels[0]
#             for other_label in ilabels:
#                 g.add_edge(label2i[ilabels[0]], label2i[label])
#         
#         # find connected components
#         clusters = nx.connected_components(g)
#         
#         # Labels in the same cluster should be marked as such
#         # Labels in two different clusters should be marked as such
#         for c, cluster in enumerate(clusters):
#             for oc, other_cluster in enumerate(clusters):
#                 status = 1 * (c == oc)
#                 for i in cluster:
#                     for j in cluster:
#                         y[i, j] = status
#         
#         # All the other pairs of labels for which we are not sure of anything
#         # will remain with a value y = -1 
#         
#         # Note that we should be able to get more 0s in this matrix.
#         
#         return y
#     
#     
#     def fit_posterior(self, inputs, outputs, features, **kwargs):
#         """
#         Train posterior
#         
#         Parameters
#         ----------
#         inputs : list of :class:`Annotation`
#         outputs : list of :class:`Annotation`
#         features : list of :class:`Feature`
#         
#         """
#         
#         self.posterior = pyfusion.normalization.bayes.Posterior(pos_label=1,
#                                                                 neg_label=0,
#                                                                 parallel=False)
#         
#         X = np.concatenate([self._get_X(iAnn, features[a]).reshape((-1,1))
#                             for a, iAnn in enumerate(inputs)])
#         y = np.concatenate([self._get_y(iAnn, outputs[a]).reshape((-1, 1)) 
#                             for a, iAnn in enumerate(inputs)])
#         self.posterior.fit(X, y=y)
#     
#     def transform_posterior(self, S):
#         """
#         
#         Parameters
#         ----------
#         S : 
#             Similarity matrix
#         
#         Returns
#         -------
#         P : 
#             Probability matrix
#         
#         """
#         
#         return self.posterior.transform(S.reshape((-1, 1))).reshape(S.shape)
    
if __name__ == "__main__":
    import doctest
    doctest.testmod()
