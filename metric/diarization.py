#!/usr/bin/env python
# encoding: utf-8

from pyannote.algorithms.hungarian import hungarian
from identification import ier

def der(reference, hypothesis):
    """
    Diarization error rate -- the lower (0.) the better.
    
    as defined in 'Fall 2004 Rich Transcription (RT-04F) Evaluation Plan'
    """

    # best mapping {hypothesis --> reference}
    mapping = hungarian(reference, hypothesis)  
    
    # translate hypothesis and compute identification error rate
    return ier(reference, hypothesis % mapping)
    