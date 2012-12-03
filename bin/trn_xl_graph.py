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
import pickle
import pyannote
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser
from pyannote.algorithm.clustering.optimization.graph import LabelCooccurrenceGraph

from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='A tool for cross-modality cooccurrence '
                                       'graph training')

def input_parser(path):
    return AnnotationParser().read(path)
    
def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)

argparser.add_argument('srcA', type=input_parser,
                       help='path to source annotation for modality A')
argparser.add_argument('tgtA', type=input_parser,
                       help='path to target annotation for modality A')
argparser.add_argument('--modalityA', type=str, default=SUPPRESS,
                       metavar='name',
                       help='rename source/target modality A')

argparser.add_argument('srcB', type=input_parser,
                       help='path to source annotation for modality B')
argparser.add_argument('tgtB', type=input_parser,
                       help='path to target annotation for modality B')
argparser.add_argument('--modalityB', type=str, default=SUPPRESS,
                       metavar='name',
                       help='rename source/target modality B')

argparser.add_argument('dump', type=output_parser, metavar='dump_to',
                        help='path where to save parameters of trained '
                             'cross-modal cooccurrence graph')

argparser.add_argument('--duration', metavar='seconds', type=float, default=0.,
                       help='Minimum cooccurrence duration for two labels to '
                            'be considered cooccurring (default is 0 second)')

argparser.add_argument('--significant', metavar='N', type=int, default=50,
                       help='Blah blah (default is 50.)')

try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

# if requested, use provided resources
if hasattr(args, 'uris'):
    uris = args.uris
# otherwise, use 
else:
    uris = args.srcA.uris

def aAbBiterator():
    for u, uri in enumerate(uris):
        
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()
        
        srcA = args.srcA(uri)
        tgtA = args.tgtA(uri)
        if hasattr(args, 'modalityA'):
            srcA.modality = args.modalityA
            tgtA.modality = args.modalityA
        
        srcB = args.srcB(uri)
        tgtB = args.tgtB(uri)
        if hasattr(args, 'modalityB'):
            srcB.modality = args.modalityB
            tgtB.modality = args.modalityB
        
        if hasattr(args, 'uem'):
            srcA = srcA.crop(args.uem(uri), mode='intersection')
            tgtA = tgtA.crop(args.uem(uri), mode='intersection')
            srcB = srcB.crop(args.uem(uri), mode='intersection')
            tgtB = tgtB.crop(args.uem(uri), mode='intersection')
        
        yield tgtA, srcA, tgtB, srcB

labelCooccurrenceGraph = LabelCooccurrenceGraph(minduration=args.duration,
                                                significant=args.significant)
labelCooccurrenceGraph.fit(aAbBiterator())

data = {}
data['modalityA'] = labelCooccurrenceGraph.modalityA
data['modalityB'] = labelCooccurrenceGraph.modalityB
data['minduration'] = labelCooccurrenceGraph.minduration
data['# matches'] = labelCooccurrenceGraph.num_matches
data['# times'] = labelCooccurrenceGraph.num_times
data['P'] = labelCooccurrenceGraph.P

pickle.dump(data, args.dump)
args.dump.close()

