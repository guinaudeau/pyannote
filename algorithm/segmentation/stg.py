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


from base import BaseSegmenter
import numpy as np

import scipy.spatial.distance
import scipy.cluster.hierarchy


class TransitionGraphSegmenter(BaseSegmenter):
    """Temporal segmentation based on Transition Graph
    
    
    
    References
    ----------
    
    """
    @classmethod
    def train(cls, feature, true_segmentation):
        
        
        
    
    def __init__(self):
        super(TransitionGraphSegmenter, self).__init__()
    
    
    def _compute_df(self, feature, timeline, distance):
        """Pre-compute feature distance dendrogram
        
        Parameters
        ----------
        feature : 
        
        timeline : 
            Temporal units
        distance : 
        
        """
        
        # initialize feature distance matrix with zeros
        n = len(timeline)
        M = np.zeros((n, n))
        
        for s, segment in enumerate(timeline):
            
            s_feature = feature[segment]
            
            for t in range(s+1, n):
                
                t_feature = feature[timeline[t]]
                
                # feature distance between two segments
                M[s, t] = distance(s_feature, t_feature)
                
                # feature distance is symmetric
                M[t, s] = M[s, t]
        
        y = scipy.spatial.distance.squareform(M, checks=False)
        df = scipy.cluster.hierarchy.complete(y)
        return df
    
    def _compute_dt(self, timeline):
        """Pre-compute temporal distance matrix
        
        Parameters
        ----------
        timeline : :class:`pyannote.base.timeline.Timeline`
            Temporal units.
            
        Returns
        -------
        dt : numpy array
            Temporal distance for each pair of segments in `timeline`,
            computed as the duration of the gap between them.
            
        Examples
        --------
        
            >>> segmenter = TransitionGraphSegmenter()
            >>> timeline = Timeline() + Segment(0, 1) + Segment(4, 5)
            >>> print segmenter._dt(timeline)
            [[0, 3], [3, 0]]
            
        """
        
        # initialize temporal distance matrix with zeros
        n = len(timeline)
        dt = np.zeros((n, n))
        
        for s, segment in enumerate(timeline):
            # no need to set dt[s, s] to 0 
            # as it is already initialized as such
            
            for t in range(s+1, n):
                
                # temporal distance between two segments is gap duration
                dt[s, t] = (s^t).duration
                
                # matrix is obviously symmetrical
                dt[t, s] = dt[s, t]
        
        return dt
        
    
    
    
    
    
    def __segment(self, feature, units=None, distance=None, \
                  precomputed_dt=False, precomputed_df=False, \
                  threshold_dt=None, threshold_df=None):
        """
        
        Parameters
        ----------
        feature : :class:`pyannote.base.feature.TimelineFeature`
        
        units : :class:`pyannote.base.timeline.Timeline` or None
            If None, 
            
        distance : func
            Distance between features
        
        precomputed_dt : bool, optional
            If False, temporal distance matrix is computed & stored internally
            If True, stored temporal distance matrix is used.
        
        precomputed_df : bool, optional
            If False, feature distance dendrogram is computed 
            & stored internally
            If True, stored feature distance dendrogram is used.
        
        Returns
        -------
        partition : :class:`pyannote.base.timeline.Timeline`
        
        """
        
        # by default, use feature internal timeline as units
        if units is None:
            units = feature.timeline
        
        # by default, use feature internal distance as distance between feature
        if distance is None:
            distance = feature.distance
        
        # compute temporal distance matrix only if needed
        if precomputed_dt is None:
            self._tdistance = self._compute_dt(units)
        
        # compute feature distance dendrogram only if needed
        if precomputed_df is None:
            self._fdendrogram = self._compute_df(feature, units, distance)
        
        # flatten dendrogram based on df_threshold
        self._fcluster = scipy.cluster.hierarchy.fcluster(self._df, \
                                                    threshold_df, \
                                                    criterion='distance')
        
        
        
        
        

class GeneralizedTransitionGraphSegmenter(TransitionGraphSegmenter):
    """Temporal segmentation based on Generalized Transition Graph
    
    
    References
    ----------
    
    """
    def __init__(self):
        super(GeneralizedTransitionGraphSegmenter, self).__init__()
        self.arg = arg
    
    def fit(self, X, y):
        
        time_distance = {}
        time_thresholds = set([])
        
        feat_distance = {}
        feat_thresholds = set([])
        
        for f, feature in enumerate(X):
            
            # compute temporal distance matrix
            # and keep track of min/max
            time_distance[f] = self._compute_time_distance(feature)
            time_thresholds |= set(squareform(time_distance[f], checks=False))
            
            
            feat_distance[f] = self._compute_feat_distance(feature)
            feat_thresholds |= set(squareform(feat_distance[f], checks=False))
        
        
        # generate every temporal matrix Mt
        
        # generate every feature matrix Mf
        # get list of possible values for Mt threshold
        # get list of possible values for Mf threshold
        
        # for each video
            # compute temporal matrix Mt
            # compute feature matrix Mf
            # for each temporal distance threshold
                # binarize Mt (zero if lower than threshold, +inf if higher)
                # M = binarized Mt + Mf
                # for each feature distance threshold
                    # 
        
        
        
        