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
from argparse import ArgumentParser

argparser = ArgumentParser(description='A tool for evaluation of (speaker) diarization')
argparser.add_argument('--version', action='version', 
                    version=('PyAnnote %s' % pyannote.__version__))

import pyannote.parser
def groundtruth_parser(path):
    return pyannote.parser.AnnotationParser().read(path)
def hypothesis_parser(path):
    return (path, pyannote.parser.AnnotationParser().read(path))
def uem_parser(path):
    return pyannote.parser.TimelineParser().read(path)

argparser.add_argument('groundtruth', type=groundtruth_parser,
                       help='path to groundtruth diarization')
argparser.add_argument('hypothesis', nargs='+', type=hypothesis_parser,
                        help='path to automatic diarization')
argparser.add_argument('--uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM)')
argparser.add_argument('--purity', action='store_true',
                       help='compute diarization purity')
argparser.add_argument('--coverage', action='store_true',
                       help='compute diarization coverage')
argparser.add_argument('--homogeneity', action='store_true',
                       help='compute diarization homogeneity')
argparser.add_argument('--completeness', action='store_true',
                       help='compute diarization completeness')
args = argparser.parse_args()


from prettytable import PrettyTable
header = ['', 'DER']

import pyannote.metric
der = [pyannote.metric.DiarizationErrorRate() 
       for _ in args.hypothesis]

if args.purity:
    header.append('Purity')
    purity = [pyannote.metric.diarization.DiarizationPurity() 
              for _ in args.hypothesis]
if args.coverage:
    header.append('Coverage')
    coverage = [pyannote.metric.diarization.DiarizationCoverage() 
                for _ in args.hypothesis]
if args.homogeneity:
    header.append('Homogeneity')
    homogeneity = [pyannote.metric.diarization.DiarizationHomogeneity() 
                   for _ in args.hypothesis]
if args.completeness:
    header.append('Completeness')
    completeness = [pyannote.metric.diarization.DiarizationCompleteness() 
                    for _ in args.hypothesis]

table = PrettyTable(header)
table.float_format = '1.3'
table.align[''] = 'l'

for uri in args.groundtruth.videos:
    
    ref = args.groundtruth(uri)
    
    if args.uem is None:
        uem = None
    else:
        uem = args.uem(uri)
    
    if uem is not None:
        ref = ref(uem, mode='intersection')
    
    for h, (path, hypothesis) in enumerate(args.hypothesis):
        
        if len(args.hypothesis) > 1:
            row = ['%s [%d]' % (uri, h+1) ]
        else:
            row = ['%s' % uri]
            
        hyp = hypothesis(uri)
        if uem is not None:
            hyp = hyp(uem, mode='intersection')
        
        D = der[h](ref, hyp)
        row.append(D)
        
        if args.purity:
            P = purity[h](ref, hyp)
            row.append(P)
        if args.coverage:
            C = coverage[h](ref, hyp)
            row.append(C)
        if args.homogeneity:
            H = homogeneity[h](ref, hyp)
            row.append(H)
        if args.completeness:
            K = completeness[h](ref, hyp)
            row.append(K)
        
        table.add_row(row)

print table
if len(args.hypothesis) > 1:
    for h, (path, _) in enumerate(args.hypothesis):
        print '[%d] %s' % (h+1, path)
    print

table = PrettyTable(header)
table.align[''] = 'l'
table.float_format = '1.3'

import os.path
prefix = os.path.commonprefix([path for path, _ in args.hypothesis])
length = len(prefix)

for h, (path, _) in enumerate(args.hypothesis):
    
    row = [path[length:], abs(der[h])]
    if args.purity:
        row.append(abs(purity[h]))
    if args.coverage:
        row.append(abs(coverage[h]))
    if args.homogeneity:
        row.append(abs(homogeneity[h]))
    if args.completeness:
        row.append(abs(completeness[h]))
    
    table.add_row(row)

print table

