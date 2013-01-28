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
from pyannote.base.annotation import Annotation, Scores, Unknown
from pyannote.parser import AnnotationParser, LSTParser
from pyannote.algorithm.util.calibration import IDScoreCalibration
from pyannote.algorithm.tagging import ArgMaxDirectTagger

def train_speaker_calibration(args):
    
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


def train_head_calibration(args):
    
    if hasattr(args, 'uris'):
        uris = args.uris
    else:
        raise ValueError('missing uri list')
    
    references = []
    scores = []
    targets = None
    
    for u, uri in enumerate(uris):
        
        if args.verbose:
            sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
            sys.stdout.flush()
        
        reference = args.references(uri)
        score = args.scores(uri)
        
        if not targets:
            targets = score.labels()
        
        new_r = Annotation(uri=reference.uri, modality=reference.modality)
        new_s = Scores(uri=score.uri, modality=score.modality)
        
        for s,t,l in reference.iterlabels():
            if isinstance(l, Unknown):
                continue
            s_t = score.get_track_by_name(t)
            if not s_t:
                continue
            for L,v in score.get_track_scores(*(s_t[0])).iteritems():
                new_r[s, t] = l
                new_s[s, t, L] = v
        
        reference = new_r
        score = new_s
        
        if hasattr(args, 'uem'):
            reference = reference.crop(args.uem(uri), mode='loose')
            score = score.crop(args.uem(uri), mode='loose')
        
        references.append(reference)
        scores.append(score)
    
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
subparsers = argparser.add_subparsers(help='mode')

# calibration train speaker
train_parser = subparsers.add_parser('train', help='Train calibration')

train_subparsers = train_parser.add_subparsers(help='modality')
train_speaker_parser = train_subparsers.add_parser('speaker', parents=[clicommon.parser],
                                                   help='Speaker identification')
train_speaker_parser.set_defaults(func=train_speaker_calibration)

annotation_parser = lambda path: AnnotationParser().read(path)
train_speaker_parser.add_argument('references', metavar='file.mdtm', 
                          type=annotation_parser, help='path to references')
                          
def scores_parser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)
msg = "path to identification scores. " + clicommon.msgURI()
train_speaker_parser.add_argument('scores', metavar='scores.etf0|[URI].tvm',
                          type=scores_parser, help=msg)

train_speaker_parser.add_argument('output', metavar='calibration.pkl',
                          type=str, help='path to calibration file')

list_parser = lambda path: LSTParser().read(path)
train_speaker_parser.add_argument('--targets', metavar='targets.lst', default=SUPPRESS,
                          type=list_parser, help='path to list of targets')

# calibration train head
train_head_parser = train_subparsers.add_parser('head', parents=[clicommon.parser],
                                                 help='Face recognition')
train_head_parser.set_defaults(func=train_head_calibration)

def input_fparser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser(load_ids=True)\
                         .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        raise IOError('Only .facetracks input files are supported for now.')

msg = "path to input associated tracks. " + clicommon.msgURI()
train_head_parser.add_argument('references', metavar='[URI].facetracks', 
                               type=input_fparser, help='path to references')

msg = "path to identification scores. " + clicommon.msgURI()
train_head_parser.add_argument('scores', metavar='scores.etf0|[URI].tvm',
                          type=scores_parser, help=msg)

train_head_parser.add_argument('output', metavar='calibration.pkl',
                               type=str, help='path to calibration file')


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
