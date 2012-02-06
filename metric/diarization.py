#!/usr/bin/env python
# encoding: utf-8

from pyannote.algorithms.hungarian import hungarian

def der(reference, hypothesis):
    """
    Diarization error rate -- the lower (0.) the better.
    
    as defined in 'Fall 2004 Rich Transcription (RT-04F) Evaluation Plan'
    """

    # best mapping {hypothesis --> reference}
    mapping = hungarian(reference, hypothesis)  
    
    # common (up-sampled) timeline
    common_timeline = abs(reference.timeline + hypothesis.timeline)
    
    # align reference on common timeline
    R = reference >> common_timeline
    
    # translate and align hypothesis on common timeline
    H = (hypothesis % mapping) >> common_timeline
    
    total = 0.
    error = 0.
    miss = 0.
    fa = 0.
    
    # loop on all segments
    for segment in common_timeline:
        
        # --- local IDs ---
        
        # set of IDs in reference segment
        r = R.ids(segment) if segment in R else set([])
        Nr = len(r)
        
        # set of IDs in hypothesis segment
        h = H.ids(segment) if segment in H else set([])
        Nh = len(h)
        
        # --- local errors ---
        # local errors
        
        # number of correct matches
        N_correct = len(r & h)
        
        # number of incorrect matches
        N_error   = min(Nr, Nh) - N_correct
        
        # number of misses
        N_miss = max(0, Nr - Nh)
        
        # number of false alarms
        N_fa = max(0, Nh - Nr)
        
        # --- global errors ---
        
        # segment duration
        duration = abs(segment)
        
        # total duration in reference
        total += duration * Nr
        
        # total match error
        error += duration * N_error
        
        # total misses
        miss += duration * N_miss
        
        # total false alarms
        fa += duration * N_fa
    
    return (error + miss + fa) / total
