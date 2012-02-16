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
        raise TypeError('Reference must be either None or a Mapping, not %s.' % type(hypothesis).__name__)
    
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

    
    
    
# def association_error_rate(source, target, mapping, weights=None):
#     
#     """
#     :param source: 
#     :type source: list or set
#     :param target:
#     :type target:
#     :param mapping: {source --> target} dictionary. 
#     :type mapping: dictionary
#     
#     Typically,
#         >>> source = modality1.IDs
#         >>> target = modality2.IDs
#         >>> mapping = hungarian(source, target)
#         >>> weights = {s: modality1(s).timeline.duration() for s in source}
#         >>> association_error_rate(source, target, mapping, weights)
#     
#     """
#     
#     # list of source IDs that actually have a match in target
#     should_be_mapped = set(source) & set(target)
#     
#     if not weights:
#         weights = {}
#         for s in source:
#             weights[s] = 1
#     
#     for s in source:
#         if s not in mapping:
#             mapping[s] = NoMatch()
#     
#     miss = 0.
#     fa = 0.
#     error = 0.
#     total = 0.
#     
#     for s in source:
#         total += weights[s]
#         if s in should_be_mapped:
#             if isinstance(mapping[s], NoMatch):
#                 miss += weights[s]
#             else:
#                 if mapping[s] != s:
#                     error += weights[s]
#         elif not isinstance(mapping[s], NoMatch):
#             fa += weights[s]
#                 
#     return 1. * (miss + fa + error) / total
    