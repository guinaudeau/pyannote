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

# argparser.add_argument('--detection', metavar='detection.mdtm',
#                        type=in_parser, default=SUPPRESS,
#                        help='when provided, the oracle relies on this '
#                             'detection. otherwise, it uses the reference.')

def model_parser(path):
    models = set(LSTParser().read(path))
    return models
    
argparser.add_argument('--models', metavar='models.lst',
                       type=model_parser, default=[], 
                       action='append', dest='models',
                       help='when provided, the oracle perfectly recognizes '
                            'the persons whose model is in the list.')

def train_parser(path):
    models = set([])
    parser = AnnotationParser().read(path)
    for uri in parser.videos:
        models.update(parser(uri).labels())
    return models

argparser.add_argument('--training', metavar='training.mdtm',
                       type=train_parser, default=[], 
                       action='append', dest='models',
                       help='when provided, the oracle perfectly recognizes '
                            'the persons appearing at least once in the '
                            'training set.')

argparser.add_argument('--cross', metavar='cross.mdtm', 
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

# merge every list of models
global_models = set([])
for labels in args.models:
    global_models.update(labels)

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
                annotation = annotation(uem, mode='intersection')
            labels = annotation.labels()
            local_models.update(labels)
    
    reference = args.reference(uri)
    if uem is not None:
        reference = reference(uem, mode='intersection')
    
    translation = {}
    for label in reference.labels():
        if label not in global_models and label not in local_models:
            translation[label] = Unknown()
    
    MDTMParser().write(reference % translation, f=args.output)

args.output.close()

