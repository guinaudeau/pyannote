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
import networkx as nx
from argparse import ArgumentParser, SUPPRESS
from pyannote import clicommon
from pyannote.parser import AnnotationParser, LSTParser, MDTMParser
from pyannote.base.annotation import Unknown
from pyannote.algorithm.tagging import ArgMaxDirectTagger

argparser = ArgumentParser(parents=[clicommon.parser],
                           description='One oracle to rule them all')

def in_parser(path):
    """"""
    return AnnotationParser().read(path)

argparser.add_argument('reference', type=in_parser, metavar='reference.mdtm',
                       help='the oracle aims at this reference annotation')

def out_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
argparser.add_argument('output', type=out_parser, metavar='output.mdtm',
                       help='path to where to store output in MDTM format')

argparser.add_argument('--detection', metavar='detection.mdtm',
                       type=in_parser, default=SUPPRESS,
                       help='when provided, the oracle relies on this '
                            'detection. otherwise, it uses the reference.')

def model_parser(path):
    models = set(LSTParser().read(path))
    return models


group = argparser.add_argument_group('Supervised oracle')
group.add_argument('--models', metavar='models.lst',
                       type=model_parser, default=[], 
                       action='append', dest='models',
                       help='when provided, the oracle perfectly recognizes '
                            'the persons whose model is in the list.')
group.add_argument('--training', metavar='training.mdtm',
                       type=str, default=SUPPRESS,
                       help='when provided, the oracle perfectly recognizes '
                            'any person appearing in the training set.')
group.add_argument('--at-least', metavar='N', type=int, default=1,
                   help='the oracle needs at least N occurrences of a person '
                        'in the training set to be able to recognize it.')

group = argparser.add_argument_group('Unsupervised oracle')
group.add_argument('--cross', metavar='cross.mdtm', 
                       type=in_parser, default=[],
                       action='append', dest='cross',
                       help='when provided, the oracle is able to recognize '
                            'persons accross modalities.')

try:
    args = argparser.parse_args()
except IOError as e:
    sys.exit(e)

if hasattr(args, 'uris'):
    uris = args.uris

global_models = set([])

# obtain trained models with at least N occurrences.
if hasattr(args, 'training'):
    parser = AnnotationParser().read(args.training)
    noccurrences = {}
    for uri in parser.uris:
        annotation = parser(uri)
        for label in annotation.labels():
            n = len(annotation.label_timeline(label, copy=False))
            if label not in noccurrences:
                noccurrences[label] = 0
            noccurrences[label] += n
    for label in noccurrences:
        if noccurrences[label] >= args.at_least:
            global_models.add(label)

# add other list of models
for labels in args.models:
    global_models.update(labels)

if hasattr(args, 'detection'):
    argMaxDirectTagger = ArgMaxDirectTagger(known_first=True)

for u, uri in enumerate(uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    if hasattr(args, 'uem'):
        uem = args.uem(uri)
    else:
        uem = None
    
    # get list of persons recognizable accross modalities
    local_models = set([])
    if args.cross:
        for cross in args.cross:
            annotation = cross(uri)
            if uem is not None:
                annotation = annotation.crop(uem, mode='intersection')
            labels = annotation.labels()
            local_models.update(labels)
    
    reference = args.reference(uri)
    
    if uem is not None:
        reference = reference.crop(uem, mode='intersection')
    
    if hasattr(args, 'detection'):
        detection = args.detection(uri)
        
        if detection.modality != reference.modality:
            sys.exit('ERROR: reference/detection modality mismatch ' 
                     '(%s vs. %s)' % (reference.modality, detection.modality))
        
        if uem is not None:
            detection = detection.crop(uem, mode='intersection')
        timeline = (reference.timeline + detection.timeline).segmentation()
        reference = argMaxDirectTagger(reference >> timeline, 
                                       detection >> timeline)
    
    translation = {}
    for label in reference.labels():
        if label not in global_models and label not in local_models:
            translation[label] = Unknown()
    
    MDTMParser().write(reference % translation, f=args.output)

args.output.close()

