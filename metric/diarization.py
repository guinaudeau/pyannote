#!/usr/bin/env python
# encoding: utf-8

from pyannote.algorithms.association.hungarian import hungarian
from identification import identification_error_rate

def diarization_error_rate(reference, hypothesis):
    """
    Diarization error rate -- the lower (0.) the better.
    
    as defined in 'Fall 2004 Rich Transcription (RT-04F) Evaluation Plan'
    """

    # best mapping {hypothesis --> reference}
    mapping = hungarian(hypothesis, reference).to_dict()  
    
    # translate hypothesis and compute identification error rate
    return identification_error_rate(reference, hypothesis % mapping)

def der(reference, hypothesis):
    return diarization_error_rate(reference, hypothesis)
