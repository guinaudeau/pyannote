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
Label tagging algorithms are defined in module 
``pyannote.algorithm.tagging.label``.

They can be used to propagate labels from one ``Annotation`` (called `source`) 
to another ``Annotation`` (called `target`). 

They act as translation algorithms where each `target` label is either given a unique `source` label translation or left unchanged.

"""

from base import BaseTagger
from pyannote.base.mapping import ManyToOneMapping
from pyannote.algorithm.mapping.hungarian import HungarianMapper
from pyannote.algorithm.mapping.argmax import ArgMaxMapper

class LabelTagger(BaseTagger):
    """Generic label tagging.
    
    Label tagging algorithms are made of two steps:
        - first, a label mapping algorithm is applied to find the optimal
          mapping between target labels and source labels.
        - then, any target label with a corresponding source label is translated
          using this optimal mapping.
    
    Parameters
    ----------
    mapper : any BaseMapper subclass
        Mapping algorithm used to find the optimal mapping between source and 
        target labels.
    
    See Also
    --------
    :class:`pyannote.algorithm.mapping.base.BaseMapper` 
    
    """
    def __init__(self, mapper):
        
        # Label tagging algorithm cannot tag timelines (only annotation).
        super(LabelTagger, self).__init__(annotation=True, timeline=False)
        
        # keep track of mapper
        self.__mapper = mapper
    
    def _tag_annotation(self, source, target):
        """Perform the actual tagging.
        
        Parameters
        ----------
        source, target : :class:`pyannote.base.annotation.Annotation`
        
        Returns
        -------
        tagged : :class:`pyannote.base.annotation.Annotation`
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
    """Label tagging based on the Hungarian label mapping algorithm.
    
    Relies on the Hungarian mapping algorithm to find the optimal one-to-one
    mapping between `target` and `source` labels.
    
    Parameters
    ----------
    cost : type
        Cost function for Hungarian mapping algorithms.
        Defaults to :class:`pyannote.base.matrix.Cooccurrence`.
    
    Examples
    --------
        >>> tagger = HungarianTagger(confusion=Cooccurrence)
        >>> tagged_target = tagger(source, target)
        
    See Also
    --------
    :class:`LabelTagger`
    :class:`pyannote.algorithm.mapping.hungarian.HungarianMapper`
    
    """
    def __init__(self, cost=None):
        mapper = HungarianMapper(cost=cost)
        super(HungarianTagger, self).__init__(mapper)


class ArgMaxTagger(LabelTagger):
    """Label tagging based on the ArgMax label mapping algorithm.
    
    Relies on the ArgMax mapping algorithm to find the optimal many-to-one
    mapping between `target` and `source` labels.
    
    Parameters
    ----------
    cost : type
        Defaults to Cooccurrence.
    
    Examples
    --------
        >>> tagger = ArgMaxTagger(confusion=CoTFIDF)
        >>> tagged_target = tagger(source, target)
    
    See Also
    --------
    :class:`LabelTagger`
    :class:`pyannote.algorithm.mapping.argmax.ArgMaxMapper`
    
    """
    def __init__(self, cost=None):
        mapper = ArgMaxMapper(cost=cost)
        super(ArgMaxTagger, self).__init__(mapper)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
