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

from pyannote.base.segment import SlidingWindow

class BaseSegmenter(object):
    def __init__(self):
        super(BaseSegmenter, self).__init__()

class PeriodicSegmenter(BaseSegmenter):
    def __init__(self, period):
        super(PeriodicSegmenter, self).__init__()
        self.__period = period
        
    def __get_period(self):
        return self.__period
    def __set_period(self, value):
        self.__period = value
    period = property(fget=__get_period, \
                      fset=__set_period, \
                      fdel=None, \
                      doc='Segmentation period.')
    
    def __call__(self, feature):
        """
        
        Parameters
        ----------
        feature : :class:`pyannote.base.feature.BaseFeature`
        
        Returns
        -------
        segmentation : :class:`pyannote.base.timeline.Timeline`
        
        
        """
        
        extent = feature.extent()
        sliding_window = SlidingWindow(duration=self.period, \
                                       step=self.period, \
                                       start=extent.start, \
                                       end=extent.end)
        segmentation = Timeline(uri=feature.uri)
        for window in sliding_window:
            segmentation += window
        return segmentation
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()

        