#!/usr/bin/env python
# encoding: utf-8

"""


S is the set of IDs in source modality.
T is the set of IDs in target modality.

Cross-modal association consists in finding, for each ID s in S the corresponding ID t in T if s actually h 


"""
from pyannote.algorithms.association import NoMatch

def association_error_rate(source, target, mapping, weights=None):
    
    """
    :param source: 
    :type source: list or set
    :param target:
    :type target:
    :param mapping: {source --> target} dictionary. 
    :type mapping: dictionary
    
    Typically,
        >>> source = modality1.IDs
        >>> target = modality2.IDs
        >>> mapping = hungarian(source, target)
        >>> weights = {s: modality1(s).timeline.duration() for s in source}
        >>> association_error_rate(source, target, mapping, weights)
    
    """
    
    # list of source IDs that actually have a match in target
    should_be_mapped = set(source) & set(target)
    
    if not weights:
        weights = {}
        for s in source:
            weights[s] = 1
    
    for s in source:
        if s not in mapping:
            mapping[s] = NoMatch()
    
    miss = 0.
    fa = 0.
    error = 0.
    total = 0.
    
    for s in source:
        total += weights[s]
        if s in should_be_mapped:
            if isinstance(mapping[s], NoMatch):
                miss += weights[s]
            else:
                if mapping[s] != s:
                    error += weights[s]
        elif not isinstance(mapping[s], NoMatch):
            fa += weights[s]
                
    return 1. * (miss + fa + error) / total
    