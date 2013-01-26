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
import numpy as np
import pickle
from pyannote import clicommon
from pyannote.base.annotation import Scores
from pyannote.parser import AnnotationParser, LSTParser
from pyannote.algorithm.util.calibration import IDScoreCalibration
from pyannote.algorithm.tagging import ArgMaxDirectTagger

def train_calibration(args):
    
    if hasattr(args, 'uris'):
        uris = args.uris
    else:
        uris = args.references.uris
    
    if hasattr(args, 'targets'):
        targets = set(args.targets)
    else:
        targets = set([])
    
    tagger = ArgMaxDirectTagger()
    
    references = []
    scores = []
    
    for uri in uris:
        
        r = args.references(uri)
        s = args.scores(uri)
        
        # focus on tracks with scores for targets
        if not hasattr(args, 'targets'):
            if not targets:
                targets = set(s.labels())
        else:
            new_s = Scores(uri=s.uri, modality=s.modality)
            for s,t,l,v in s.itervalues():
                if np.isnan(v):
                    continue
                if l in targets:
                    new_s[s,t,l] = v
            s = new_s
        
        if hasattr(args, 'uem'):
            coverage = (args.uem(uri) & r.timeline & s.timeline).coverage()
        else:
            coverage = (r.timeline & s.timeline).coverage()
        
        s = s.crop(coverage, mode='intersection')
        r = tagger(r, s.to_annotation(threshold=np.inf))
        
        references.append(r)
        scores.append(s)
    
    calibration = IDScoreCalibration().fit(targets, references, scores)
    
    with open(args.output, 'w') as f:
        pickle.dump(calibration, f)


def apply_calibration(args):
    
    if hasattr(args, 'uris'):
        uris = args.uris
    else:
        uris = args.references.uris
    
    calibration = args.calibration
    targets = calibration.targets
    
    writer, f = args.output
    
    for uri in uris:
        
        s = args.scores(uri)
        
        # only keep tracks with scores for targets
        new_s = Scores(uri=s.uri, modality=s.modality)
        for s,t,l,v in s.itervalues():
            if np.isnan(v):
                continue
            if l in targets:
                new_s[s,t,l] = v
        s = new_s
        
        # focus on uem if requested
        if hasattr(args, 'uem'):
            s = s.crop(args.uem(uri), mode='intersection')
        
        # actual score calibration
        calibrated = args.calibration(s)
        
        # write calibrated scores to output file
        writer.write(calibrated, f=f)
    
    f.close()

argparser = ArgumentParser(description='Identification scores calibration')
subparsers = argparser.add_subparsers(help='commands')

# calibration train
train_parser = subparsers.add_parser('train', parents=[clicommon.parser], 
                                     help='Train calibration')
train_parser.set_defaults(func=train_calibration)

annotation_parser = lambda path: AnnotationParser().read(path)
train_parser.add_argument('references', metavar='file.mdtm', 
                          type=annotation_parser, help='path to references')
                          
def scores_parser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)
msg = "path to identification scores. " + clicommon.msgURI()
train_parser.add_argument('scores', metavar='scores.etf0|[URI].tvm',
                          type=scores_parser, help=msg)

train_parser.add_argument('output', metavar='calibration.pkl',
                          type=str, help='path to calibration file')

list_parser = lambda path: LSTParser().read(path)
train_parser.add_argument('--targets', metavar='targets.lst', default=SUPPRESS,
                          type=list_parser, help='path to list of targets')

# calibration apply
apply_parser = subparsers.add_parser('apply', parents=[clicommon.parser],
                                     help='Apply calibration')
apply_parser.set_defaults(func=apply_calibration)

msg = "path to identification scores. " + clicommon.msgURI()
apply_parser.add_argument('scores', metavar='file.etf0|[URI].tvm',
                          type=scores_parser, help='path to scores')

def calibration_parser(path):
    with open(path, 'r') as f:
        calibration = pickle.load(f)
    return calibration
apply_parser.add_argument('calibration', metavar='calibration.pkl',
                          type=calibration_parser, 
                          help='path to calibration file')

def output_parser(path):
    try:
        with open(path) as f: pass
    except IOError as e:
        writer, extension = AnnotationParser.guess(path)
        return writer(), open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
apply_parser.add_argument('output', metavar='calibrated.etf0',
                          type=output_parser, help='path to calibrated scores')


# Actual argument parsing
try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)
