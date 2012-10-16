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

import sys
from argparse import ArgumentParser, SUPPRESS
from progressbar import ProgressBar, Bar, ETA
import numpy as np
import pyannote
from pyannote.metric.diarization import DiarizationErrorRate, \
                                        DiarizationPurity, \
                                        DiarizationCoverage, \
                                        DiarizationCompleteness, \
                                        DiarizationHomogeneity
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.base.matrix import LabelMatrix

argparser = ArgumentParser(description='A tool for evaluation of annotations')
argparser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))


def groundtruth_parser(path):
    return AnnotationParser().read(path)

def hypothesis_parser(path):
    return (path, AnnotationParser().read(path))

def uem_parser(path):
    return TimelineParser().read(path)

def uris_parser(path):
    return LSTParser().read(path)

# First positional argument is groundtruth file
# It is loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('groundtruth', type=groundtruth_parser,
                       help='path to groundtruth')

# Next positional arguments (at least one) are hypothesis files
# They are loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('hypothesis', nargs='+', type=hypothesis_parser,
                        help='path to hypothesis')

argparser.add_argument('--uris', type=uris_parser,
                       help='list of URI to evaluate')

# UEM file is loaded at argument-parsing time by an instance of TimelineParser
argparser.add_argument('--uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM)')

argparser.add_argument('--no-overlap', action='store_true',
                       help='remove overlapping speech regions from evaluation')

argparser.add_argument('--dump', metavar='PATH', type=str, default=SUPPRESS,
                       help='(pickle-)dump results matrices to PATH')


# Various switches to compute purity, coverage, homogeneity or completeness
# (diarization error rate is always computed)

dgroup = argparser.add_argument_group('Speaker diarization metrics')
dgroup.add_argument('--diarization', action='store_true',
                       help='compute diarization error rate')
dgroup.add_argument('--purity', action='store_true',
                       help='compute diarization purity')
dgroup.add_argument('--coverage', action='store_true',
                       help='compute diarization coverage')
dgroup.add_argument('--homogeneity', action='store_true',
                       help='compute diarization homogeneity')
dgroup.add_argument('--completeness', action='store_true',
                       help='compute diarization completeness')


# igroup = argparser.add_argument_group('Speaker identification metrics')
# igroup.add_argument('--identification', action='store_true',
#                        help='compute identification error rate')
# igroup.add_argument('--repere', action='store_true',
#                        help='compute REPERE estimated global error rate')

# Actual argument parsing
args = argparser.parse_args()

# List of requested metrics
requested = []
if args.diarization:
    requested.append(DiarizationErrorRate)
if args.purity:
    requested.append(DiarizationPurity)
if args.coverage:
    requested.append(DiarizationCoverage)
if args.homogeneity:
    requested.append(DiarizationHomogeneity)
if args.completeness:
    requested.append(DiarizationCompleteness)

# Initialize metrics & result matrix
metrics = {}
M = {}
for m in requested:
    name = m.metric_name()
    metrics[name] = {h: m() for h, (_, _) in enumerate(args.hypothesis)}
    M[name] = LabelMatrix(default=np.inf)

# only evaluate selection of uris
if args.uris:
    uris = args.uris
else:
    uris = args.groundtruth.videos

pb = ProgressBar(widgets=[Bar(),' ', ETA()], term_width=80)
pb.maxval = len(uris)*len(args.hypothesis)
pb.start()

# process each URI, one after the other
for u, uri in enumerate(uris):
    
    # read reference for current URI
    ref = args.groundtruth(uri)
    
    # read UEM if provided
    if args.uem is None:
        uem = None
    else:
        uem = args.uem(uri)
    
    # get overlapping speech regions if requested
    if args.no_overlap:
        # make sure timeline is a segmentation
        # tag each resulting segment by all intersecting labels
        tmp_ref = ref >> (ref._timeline.segmentation())
        # overlapping speech regions
        # (ie. timeline made of segments with two tracks or more)
        overlap = pyannote.Timeline([segment for segment in tmp_ref 
                                             if len(tmp_ref[segment, :]) > 1])
    
    # focus on UEM if provided
    if uem is not None:
        # update UEM if overlapping speech regions are removed from evaluation
        # remove overlapping speech regions from UEM if requested
        if args.no_overlap:
            uem = overlap.gaps(focus=uem)
        ref = ref(uem, mode='intersection')
    else:
        # remove overlapping speech regions if requested
        if args.no_overlap:
            ref = ref(overlap.gaps(focus=ref.coverage()), 
                                   mode='intersection')
    
    # process each hypothesis file, one after the other
    for h, (path, hypothesis) in enumerate(args.hypothesis):
        
        
        # read hypothesis for current URI
        hyp = hypothesis(uri)
        
        # focus on UEM if provided
        if uem is not None:
            # UEM was already updated to take overlapping speech regions
            # into account -- so no need to worry about that here.
            hyp = hyp(uem, mode='intersection')
        else:
            # remove overlapping speech regions if requested
            if args.no_overlap:
                hyp = hyp(overlap.gaps(focus=hyp.coverage()), 
                                       mode='intersection')
        
        # compute 
        for name, metric in metrics.iteritems():
            details = metric[h](ref, hyp, detailed=True)
            M[name][uri, path] = details[metric[h].name]
        
        pb.update(u*len(args.hypothesis)+h+1)

pb.finish()

AVERAGED = '__ averaged __'
COMBINED = '__ combined __'

# compute averaged & combined metric value
for name, metric in metrics.iteritems():
    for h, (path, _) in enumerate(args.hypothesis):
        M[name][AVERAGED, path] = np.mean(M[name][set(uris), path].M)
        M[name][COMBINED, path] = abs(metric[h])

# if there are more than one hypothesis
# print one table per metric, with one column per hypothesis
if len(args.hypothesis) > 1:
    for name, metric in metrics.iteritems():
        print M[name].to_table(title=name, fmt='1.3', factorize='C')
# if there is only one hypothesis
# print one single table, with one column per metric
else:
    path, _ = args.hypothesis[0]
    V = LabelMatrix(default=np.inf)
    for name, metric in metrics.iteritems():
        for uri in uris:
            V[uri, name] = M[name][uri, path]
        V[AVERAGED, name] = M[name][AVERAGED, path]
        V[COMBINED, name] = M[name][COMBINED, path]
    print V.to_table(fmt='1.3', factorize='')

if hasattr(args, 'dump'):
    import pickle
    f = open(args.dump, 'w')
    pickle.dump(M, f)
    f.close()
