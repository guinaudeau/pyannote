#!/usr/bin/env python
# encoding: utf-8

"""
"""
import sklearn.metrics
from pyannote.base.association import Mapping, OneToOneMapping

def __get_labels_true_pred(hypothesis, reference=None):
    
    if not isinstance(hypothesis, Mapping):
        raise TypeError('Hypothesis must be a Mapping, not %s.' % type(hypothesis).__name__)
    
    if reference and not isinstance(reference, Mapping):
        raise TypeError('Reference must be either None or a Mapping, not %s.' % type(reference).__name__)
    
    partition = hypothesis.to_partition()
    
    if reference:
        expected = reference.to_partition()
    else:
        expected = hypothesis.to_expected_partition()
        
    labels_true = [expected[element] for element in expected] 
    labels_pred = [partition[element] for element in expected]
    
    return labels_true, labels_pred

# -------------------------------------- #
# Many-to-many mapping evaluation metric #
# -------------------------------------- #

def homogeneity_completeness_v_measure(hypothesis, reference=None):
    labels_true, labels_pred = __get_labels_true_pred(hypothesis, reference=reference)        
    H, C, V = sklearn.metrics.homogeneity_completeness_v_measure(labels_true, labels_pred)
    return {'homogeneity': H, 'completeness': C, 'v_measure': V}

def homogeneity(hypothesis, reference=None):
    return homogeneity_completeness_v_measure(hypothesis, reference=reference)['homogeneity']

def completeness(hypothesis, reference=None):
    return homogeneity_completeness_v_measure(hypothesis, reference=reference)['completeness']
    
def v_measure(hypothesis, reference=None):
    return homogeneity_completeness_v_measure(hypothesis, reference=reference)['v_measure']

def adjusted_rand_index(hypothesis, reference=None):
    labels_true, labels_pred = __get_labels_true_pred(hypothesis, reference=reference)        
    return sklearn.metrics.adjusted_rand_score(labels_true, labels_pred)

def adjusted_mutual_info(hypothesis, reference=None):
    labels_true, labels_pred = __get_labels_true_pred(hypothesis, reference=reference)        
    return sklearn.metrics.adjusted_mutual_info_score(labels_true, labels_pred)

    
