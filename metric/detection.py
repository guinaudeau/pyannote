#!/usr/bin/env python
# encoding: utf-8

def detection_error_rate(reference, hypothesis):
    """
    Detection error rate -- the lower (0.) the better.    
    """
    
    # common (up-sampled) timeline
    common_timeline = abs(reference.timeline + hypothesis.timeline)
    
    # align reference on common timeline
    R = reference >> common_timeline
    
    # translate and align hypothesis on common timeline
    H = hypothesis >> common_timeline
    
    total = 0.
    miss = 0.
    fa = 0.
    
    # loop on all segments
    for segment in common_timeline:
        
        # --- local IDs ---
        
        # set of IDs in reference segment
        r = R.ids(segment)
        Nr = len(r)
        
        # set of IDs in hypothesis segment
        h = H.ids(segment)
        Nh = len(h)
        
        # --- local errors ---
        
        # number of misses
        N_miss = max(0, Nr - Nh)
        
        # number of false alarms
        N_fa = max(0, Nh - Nr)
        
        # --- global errors ---
        
        # segment duration
        duration = abs(segment)
        
        # total duration in reference
        total += duration * Nr
        
        # total misses
        miss += duration * N_miss
        
        # total false alarms
        fa += duration * N_fa
    
    return (miss + fa) / total
