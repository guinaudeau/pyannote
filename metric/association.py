#!/usr/bin/env python
# encoding: utf-8

"""
"""
import sklearn.metrics
from pyannote.base.association import Mapping, OneToOneMapping, NoMatch

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

# ------------------------------------ #
# One-to-one mapping evaluation metric #
# ------------------------------------ #

def __one_way_accuracy(proposed, expected):
    
    elements =  [element for element in expected if not isinstance(element, NoMatch)]
    
    correct = 0
    false_alarm = 0
    error = 0
    total = len(elements)
    
    for element in elements:
        if isinstance(proposed[element], NoMatch):
            if isinstance(expected[element], NoMatch):
                correct += 1
            else:
                false_alarm += 1
        else:
            if proposed[element] == expected[element]:
                correct += 1
            else:
                error += 1
    
    return {'total': total, 'correct': correct, 'false alarm': false_alarm, 'error': error}
    
def __get_dict_proposed_expected(hypothesis, reference=None, reverse=False):
    
    if not isinstance(hypothesis, OneToOneMapping):
        raise TypeError('Hypothesis must be a OneToOneMapping, not %s.' % type(hypothesis).__name__)
    
    if reference and not isinstance(reference, OneToOneMapping):
        raise TypeError('Reference must be either None or a OneToOneMapping, not %s.' % type(reference).__name__)
        
    proposed = hypothesis.to_dict(reverse=reverse)
    if reference:
        expected = reference.to_dict(reverse=reverse)
    else:
        expected = hypothesis.to_expected_dict(reverse=reverse)

    return proposed, expected

def accuracy(hypothesis, reference=None, detailed=False):
    
    proposed, expected = __get_dict_proposed_expected(hypothesis, reference=reference, reverse=False)
    l2r = __one_way_accuracy(proposed, expected)

    proposed, expected = __get_dict_proposed_expected(hypothesis, reference=reference, reverse=True)
    r2l = __one_way_accuracy(proposed, expected)
    
    rate = 1. * (l2r['correct'] + r2l['correct']) / (l2r['total'] + r2l['total'])
    
    if detailed:
        return {'error rate':  1. - rate, \
                'confusion':   l2r['error']+r2l['error'], \
                'false alarm': l2r['false alarm'] + r2l['false alarm'], \
                'total':       l2r['total'] + r2l['total'], \
                }
    else:
        return rate
        
