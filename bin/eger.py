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

# initialize results table
from prettytable import PrettyTable
table = PrettyTable(header)
table.float_format = '1.3'
table.align[''] = 'l'

# only evaluate selection of uris
if args.uris:
    uris = args.uris
else:
    uris = args.groundtruth.uris

# process each URI, one after the other
for uri in uris:
    
    # read reference for current URI
    ref = args.groundtruth(uri)
    
    # read annotated frame for current URI
    annotated = args.annotated(uri)
    
    # process each hypothesis file, one after the other
    for h, (path, hypothesis) in enumerate(args.hypothesis):
        
        # add URI to results table
        if len(args.hypothesis) > 1:
            row = ['%s [%d]' % (uri, h+1) ]
        else:
            row = ['%s' % uri]
        
        # read hypothesis for current URI
        hyp = hypothesis(uri)
        
        # compute EGER
        details = eger[h](ref, hyp, annotated=annotated, detailed=True)
        D = details[eger[h].name]
        row.append(D)
        
        if args.verbose:
            sys.stdout.write('%s\n' % uri)
            sys.stdout.write('%s\n' % eger[h]._pretty(details))
            sys.stdout.flush()
        
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
    table.add_row(row)

print table

# Confidence interval table
table = PrettyTable(header)
table.align[''] = 'l'

for h, (path, _) in enumerate(args.hypothesis):
    
    row = [path[length:]]
    m, (l, u) = eger[h].confidence_interval(alpha=0.9)
    row.append('%1.2f < %1.2f < %1.2f' % (l, m, u))
    
    table.add_row(row)

print table

for h, (path, _) in enumerate(args.hypothesis):
    print path[length:]
    print eger[h]
    print

