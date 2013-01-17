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
from pyannote.algorithm.mpg.graph import TrackCooccurrenceGraph

from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='A tool for cross-modality cooccurrence '
                                       'graph training')

def input_parser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser(load_ids=True)\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)


def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)

argparser.add_argument('srcA', type=input_parser,
                       help='path to annotation for modality A')
argparser.add_argument('--modalityA', type=str, default=SUPPRESS,
                       metavar='name',
                       help='rename source/target modality A')

argparser.add_argument('srcB', type=input_parser,
                       help='path to annotation for modality B')
argparser.add_argument('--modalityB', type=str, default=SUPPRESS,
                       metavar='name',
                       help='rename source/target modality B')

argparser.add_argument('dump', type=output_parser, metavar='dump_to',
                        help='path where to save parameters of trained '
                             'cross-modal cooccurrence graph')

argparser.add_argument('--min-duration', metavar='in_seconds', 
                       type=float, default=1.,
                       help='Minimum cooccurrence duration for two tracks to '
                            'be considered cooccurring (default is 1 second)')

argparser.add_argument('--significant', metavar='in_seconds', type=float, default=60.,
                       help='Blah blah (default is 60.)')

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

def ABiterator():
    for u, uri in enumerate(uris):
        
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()
        
        srcA = args.srcA(uri)
        if hasattr(args, 'modalityA'):
            srcA.modality = args.modalityA
        
        srcB = args.srcB(uri)
        if hasattr(args, 'modalityB'):
            srcB.modality = args.modalityB
        
        if hasattr(args, 'uem'):
            srcA = srcA.crop(args.uem(uri), mode='loose')
            srcB = srcB.crop(args.uem(uri), mode='loose')
        
        cvgA = srcA.timeline.coverage()
        cvgB = srcB.timeline.coverage()
        
        yield srcA.crop(cvgB, mode='loose'), srcB.crop(cvgA, mode='loose')

cooccurrenceGraph = TrackCooccurrenceGraph(min_duration=args.min_duration,
                                           significant=args.significant)
cooccurrenceGraph.fit(ABiterator())

data = {}
data['graph'] = cooccurrenceGraph
data['min_duration'] = cooccurrenceGraph.min_duration
data['significant'] = cooccurrenceGraph.significant
data['modalityA'] = cooccurrenceGraph.modalityA
data['modalityB'] = cooccurrenceGraph.modalityB
data['P'] = cooccurrenceGraph.P

pickle.dump(data, args.dump)
args.dump.close()

