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

import pyannote
import sys
from argparse import ArgumentParser

argparser = ArgumentParser(description='A tool for EGER computation')
argparser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
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
                       help='path to groundtruth file')

# Next positional argument is annotated frame uem
# It is loaded at argument-parsing time by an instance of TimelineParser
argparser.add_argument('annotated', type=uem_parser, 
                       help='path to annotated frames')

# Next positional arguments (at least one) are hypothesis files
# They are loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('hypothesis', nargs='+', type=hypothesis_parser,
                        help='path to hypothesis')

# Various switches to compute purity, coverage, homogeneity or completeness
# (diarization error rate is always computed)
argparser.add_argument('--uris', type=uris_parser,
                       help='list of URI to evaluate')

# argparser.add_argument('--coverage', action='store_true',
#                        help='compute diarization coverage')
# argparser.add_argument('--homogeneity', action='store_true',
#                        help='compute diarization homogeneity')
# argparser.add_argument('--completeness', action='store_true',
#                        help='compute diarization completeness')

# When provided, removes overlapping speech regions from evaluation
# argparser.add_argument('--no-overlap', action='store_true',
#                        help='remove overlapping speech regions from evaluation')

argparser.add_argument('--verbose', action='store_true',
                       help='print error details')

# Actual argument parsing
args = argparser.parse_args()

# initialize header of results table
header = ['', 'EGER']

# initialize EGER metric
import pyannote.metric.repere
eger = [pyannote.metric.repere.EstimatedGlobalErrorRate() 
        for _ in args.hypothesis]

# # initialize purity metric & update table header
# if args.purity:
#     header.append('Purity')
#     purity = [pyannote.metric.diarization.DiarizationPurity() 
#               for _ in args.hypothesis]

# # initialize coverage metric & update table header
# if args.coverage:
#     header.append('Coverage')
#     coverage = [pyannote.metric.diarization.DiarizationCoverage() 
#                 for _ in args.hypothesis]

# # initialize homogeneity metric & update table header
# if args.homogeneity:
#     header.append('Homogeneity')
#     homogeneity = [pyannote.metric.diarization.DiarizationHomogeneity() 
#                    for _ in args.hypothesis]

# # initialize completeness metric & update table header
# if args.completeness:
#     header.append('Completeness')
#     completeness = [pyannote.metric.diarization.DiarizationCompleteness() 
#                     for _ in args.hypothesis]

# initialize results table
from prettytable import PrettyTable
table = PrettyTable(header)
table.float_format = '1.3'
table.align[''] = 'l'

# 
if args.uris:
    uris = args.uris
else:
    uris = args.groundtruth.videos

# process each URI, one after the other
for uri in uris:
    
    # read reference for current URI
    ref = args.groundtruth(uri)
    
    # read annotated frame for current URI
    annotated = args.annotated(uri)
    
    # # get overlapping speech regions if requested
    # if args.no_overlap:
    #     # make sure timeline is a segmentation
    #     # tag each resulting segment by all intersecting labels
    #     tmp_ref = ref >> (ref._timeline.segmentation())
    #     # overlapping speech regions
    #     # (ie. timeline made of segments with two tracks or more)
    #     overlap = pyannote.Timeline([segment for segment in tmp_ref 
    #                                          if len(tmp_ref[segment, :]) > 1])
    
    # # focus on UEM if provided
    # if uem is not None:
    #     # update UEM if overlapping speech regions are removed from evaluation
    #     # remove overlapping speech regions from UEM if requested
    #     if args.no_overlap:
    #         uem = overlap.gaps(focus=uem)
    #     ref = ref(uem, mode='intersection')
    # else:
    #     # remove overlapping speech regions if requested
    #     if args.no_overlap:
    #         ref = ref(overlap.gaps(focus=ref.coverage()), 
    #                                mode='intersection')
    
    # process each hypothesis file, one after the other
    for h, (path, hypothesis) in enumerate(args.hypothesis):
        
        # add URI to results table
        if len(args.hypothesis) > 1:
            row = ['%s [%d]' % (uri, h+1) ]
        else:
            row = ['%s' % uri]
        
        # read hypothesis for current URI
        hyp = hypothesis(uri)
        
        # # focus on UEM if provided
        # if uem is not None:
        #     # UEM was already updated to take overlapping speech regions
        #     # into account -- so no need to worry about that here.
        #     hyp = hyp(uem, mode='intersection')
        # else:
        #     # remove overlapping speech regions if requested
        #     if args.no_overlap:
        #         hyp = hyp(overlap.gaps(focus=hyp.coverage()), 
        #                                mode='intersection')
        
        # compute EGER
        details = eger[h](ref, hyp, annotated=annotated, detailed=True)
        D = details[eger[h].name]
        row.append(D)
        
        if args.verbose:
            sys.stdout.write('%s\n' % uri)
            sys.stdout.write('%s\n' % eger[h]._pretty(details))
            sys.stdout.flush()
        
        # # compute purity
        # if args.purity:
        #     P = purity[h](ref, hyp)
        #     row.append(P)
        
        # # compute coverage
        # if args.coverage:
        #     C = coverage[h](ref, hyp)
        #     row.append(C)
            
        # # compute homogeneity
        # if args.homogeneity:
        #     H = homogeneity[h](ref, hyp)
        #     row.append(H)
            
        # # compute completeness
        # if args.completeness:
        #     K = completeness[h](ref, hyp)
        #     row.append(K)
        
        # update results table
        table.add_row(row)

print table
if len(args.hypothesis) > 1:
    for h, (path, _) in enumerate(args.hypothesis):
        print '[%d] %s' % (h+1, path)
    print

# Global errors table
table = PrettyTable(header)
table.align[''] = 'l'
table.float_format = '1.3'

import os.path
prefix = os.path.commonprefix([path for path, _ in args.hypothesis])
length = len(prefix)

for h, (path, _) in enumerate(args.hypothesis):
    
    row = [path[length:], abs(eger[h])]
    # if args.purity:
    #     row.append(abs(purity[h]))
    # if args.coverage:
    #     row.append(abs(coverage[h]))
    # if args.homogeneity:
    #     row.append(abs(homogeneity[h]))
    # if args.completeness:
    #     row.append(abs(completeness[h]))
    
    table.add_row(row)

print table

# Confidence interval table
table = PrettyTable(header)
table.align[''] = 'l'

for h, (path, _) in enumerate(args.hypothesis):
    
    row = [path[length:]]
    m, (l, u) = eger[h].confidence_interval(alpha=0.9)
    row.append('%1.2f < %1.2f < %1.2f' % (l, m, u))
    
    # if args.purity:
    #     m, (l, u) = purity[h].confidence_interval(alpha=0.9)
    #     row.append('%1.2f < %1.2f < %1.2f' % (l, m, u))
    # if args.coverage:
    #     m, (l, u) = coverage[h].confidence_interval(alpha=0.9)
    #     row.append('%1.2f < %1.2f < %1.2f' % (l, m, u))
    # if args.homogeneity:
    #     m, (l, u) = homogeneity[h].confidence_interval(alpha=0.9)
    #     row.append('%1.2f < %1.2f < %1.2f' % (l, m, u))
    # if args.completeness:
    #     m, (l, u) = completeness[h].confidence_interval(alpha=0.9)
    #     row.append('%1.2f < %1.2f < %1.2f' % (l, m, u))
    
    table.add_row(row)

print table
