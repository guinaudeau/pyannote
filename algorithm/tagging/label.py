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

"""
This module provides label-wise tagging algorithms. 

"""

from base import BaseTagger
from pyannote.base.mapping import ManyToOneMapping
from pyannote.algorithm.mapping.hungarian import HungarianMapper
from pyannote.algorithm.mapping.argmax import ArgMaxMapper

class LabelTagger(BaseTagger):
    """
    Label-wise tagging algorithm.
    
    Parameters
    ----------
    mapper : label mapping algorithm
    
    Returns
    -------
    tagger : LabelTagger
    
    """
    def __init__(self, mapper):
        super(LabelTagger, self).__init__(annotation=True, timeline=False)
        self.__mapper = mapper
    
    def _tag_annotation(self, source, target):
        """Perform the actual tagging.
        
        Parameters
        ----------
        source, target : Annotation
        
        Returns
        -------
        tagged : Annotation
            Tagged target.
        
        """
        
        # get many-to-one label mapping
        mapping = ManyToOneMapping.fromMapping(self.__mapper(target, source))
        
        # we only want to translate labels for which a mapping label was found.
        # the other labels are left unchanged.
        label_func = lambda x: mapping(x) if mapping(x) else x
        
        # do the actual translation
        return target.copy(label_func=label_func)


class HungarianTagger(LabelTagger):
    """
    Label-wise tagging based on Hungarian mapper.
    
    Parameters
    ----------
    confusion : Cooccurrence class or subclass, optional
        Defaults to Cooccurrence.
    """
    
    
    def __init__(self, confusion=None):
        mapper = HungarianMapper(confusion=confusion, force=False)
        super(HungarianTagger, self).__init__(mapper)


class ArgMaxTagger(LabelTagger):
    """
    Label-wise tagging based on ArgMax mapper.
    
    Parameters
    ----------
    confusion : Cooccurrence class or subclass, optional
        Defaults to Cooccurrence.
    """
    
    def __init__(self, confusion=None):
        mapper = ArgMaxMapper(confusion=confusion)
        super(ArgMaxTagger, self).__init__(mapper)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
