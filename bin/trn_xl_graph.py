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
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.algorithm.clustering.optimization.graph import LabelCooccurrenceGraph

place_holders = ["%s", "[URI]"] 

argparser = ArgumentParser(description='A tool for cross-modality cooccurrence graph training')
argparser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

def input_parser(path):
    return AnnotationParser().read(path)
def output_parser(path):
    return open(path, 'w')
def uem_parser(path):
    return TimelineParser().read(path)
def uris_parser(path):
    return LSTParser().read(path)

argparser.add_argument('srcA', type=input_parser,
                       help='path to source annotation for modality A')
argparser.add_argument('tgtA', type=input_parser,
                       help='path to target annotation for modality A')
argparser.add_argument('--modalityA', type=str, default=SUPPRESS,
                       help='force source/target modality A')

argparser.add_argument('srcB', type=input_parser,
                       help='path to source annotation for modality B')
argparser.add_argument('tgtB', type=input_parser,
                       help='path to target annotation for modality B')
argparser.add_argument('--modalityB', type=str, default=SUPPRESS,
                       help='force source/target modality B')

argparser.add_argument('dump', type=output_parser, metavar='dump_to',
                        help='path where to save parameters of trained '
                             'cross-modal cooccurrence graph')

argparser.add_argument('--uris', type=uris_parser, metavar='file.lst',
                       default=SUPPRESS, 
                       help='list of resources to use for training')

argparser.add_argument('--uem', type=uem_parser, metavar='file.uem', 
                       default=SUPPRESS,
                       help='part of resources to use for training')

argparser.add_argument('--duration', metavar='seconds', type=float, default=0.,
                       help='Minimum cooccurrence duration for two labels to be considered cooccurring (default is zero second)')

argparser.add_argument('--verbose', action='store_true',
                       help='print progress information')

args = argparser.parse_args()

# if requested, use provided resources
if hasattr(args, 'uris'):
    uris = args.uris
# otherwise, use 
else:
    uris = args.srcA.videos

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
            srcA = srcA(args.uem(uri), mode='intersection')
            tgtA = tgtA(args.uem(uri), mode='intersection')
            srcB = srcB(args.uem(uri), mode='intersection')
            tgtB = tgtB(args.uem(uri), mode='intersection')
        
        yield tgtA, srcA, tgtB, srcB

labelCooccurrenceGraph = LabelCooccurrenceGraph(minduration=args.duration)
labelCooccurrenceGraph.fit(aAbBiterator())

data = {}
data['modalityA'] = labelCooccurrenceGraph.modalityA
data['modalityB'] = labelCooccurrenceGraph.modalityB
data['minduration'] = labelCooccurrenceGraph.minduration
data['P'] = labelCooccurrenceGraph.P

pickle.dump(data, args.dump)
args.dump.close()

