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
from progressbar import ProgressBar, Bar, ETA
import numpy as np
import pyannote
from pyannote.metric.diarization import DiarizationErrorRate, \
                                        DiarizationPurity, \
                                        DiarizationCoverage, \
                                        DiarizationCompleteness, \
                                        DiarizationHomogeneity
from pyannote.metric.detection import DetectionErrorRate
from pyannote.metric.identification import IdentificationErrorRate

from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.base.matrix import LabelMatrix
from pyannote.base.annotation import Unknown

from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='A tool for evaluation')

def ref_parser(path):
    return AnnotationParser().read(path)
argparser.add_argument('groundtruth', metavar='reference', 
                       type=ref_parser, help='path to reference')

def hyp_parser(path):
    return (path, AnnotationParser().read(path))
argparser.add_argument('hypothesis', metavar='hypothesis', nargs='+',
                       type=hyp_parser, help='path to hypothesis')

argparser.add_argument('--no-overlap', action='store_true',
                       help='remove overlapping speech regions from evaluation')

argparser.add_argument('--dump', metavar='file.pkl', type=str, default=SUPPRESS,
                       help='path to (pickle-)dump results matrices to')

argparser.add_argument('--components', action='store_true',
                       help='detail error rate components')

argparser.add_argument('--modality', 
                       type=str, default=SUPPRESS, metavar="name", 
                       help='indicate which modality to evaluate. '
                            '(mandatory in case reference contains '
                            'multiple modalities)')

group = argparser.add_argument_group('Diarization & clustering')

group.add_argument('--diarization', action='append_const', dest='requested',
                                    const=DiarizationErrorRate, default=[],
                                    help='compute diarization error rate')
group.add_argument('--purity', action='append_const', dest='requested',
                                    const=DiarizationPurity, default=[],
                                    help='compute diarization purity')
group.add_argument('--coverage', action='append_const', dest='requested',
                                    const=DiarizationCoverage, default=[],
                                    help='compute diarization coverage')
group.add_argument('--homogeneity', action='append_const', dest='requested',
                                    const=DiarizationHomogeneity, default=[],
                                    help='compute clustering homogeneity')
group.add_argument('--completeness', action='append_const', dest='requested',
                                    const=DiarizationCompleteness, default=[],
                                    help='compute clustering completeness')

group = argparser.add_argument_group('Detection')
group.add_argument('--detection', action='append_const', dest='requested',
                                    const=DetectionErrorRate, default=[],
                                    help='compute detection error rate')

group = argparser.add_argument_group('Identification')
group.add_argument('--identification', action='append_const', dest='requested',
                                    const=IdentificationErrorRate, default=[],
                                    help='compute identification error rate')

group.add_argument('--unknown', choices=('remove',), default=SUPPRESS,
                   help='Unknown tracks handling.')

# Actual argument parsing
args = argparser.parse_args()
requested = args.requested
if args.components:
    if len(requested) > 1:
        sys.exit("ERROR: Option '--components' is not supported with multiple "
                 "metrics (you asked for: %s and %s)." % (", ".join([r.metric_name() for r in requested[:-1]]), requested[-1].metric_name()))
    if len(args.hypothesis) > 1:
        sys.exit("ERROR: Option '--components' is not supported with multiple "
                 "hypothesis (you asked for %d)." % len(args.hypothesis))

# Initialize metrics & result matrix
metrics = {}
M = {}

for m in requested:
    name = m.metric_name()
    metrics[name] = {h: m() for h, (_, _) in enumerate(args.hypothesis)}
    M[name] = LabelMatrix(default=np.inf)

if args.components:
    C = {}
    for m in requested:
        name = m.metric_name()
        C[name] = {c: LabelMatrix(default=np.inf) 
                   for c in m.metric_components()}

# only evaluate selection of uris
if args.uris:
    uris = args.uris
else:
    uris = args.groundtruth.videos

pb = ProgressBar(widgets=[Bar(),' ', ETA()], term_width=80)
pb.maxval = len(uris)*len(args.hypothesis)
pb.start()

if hasattr(args, 'modality'):
    modality = args.modality
else:
    if len(args.groundtruth.modalities) > 1:
        sys.exit("ERROR: reference contains more than one modality. "
                 "use option --modality.")
    modality = None

# process each URI, one after the other
for u, uri in enumerate(uris):
    
    
    # read reference for current URI
    ref = args.groundtruth(video=uri, modality=modality)
    
    # read UEM if provided
    if args.uem is None:
        uem = None
    else:
        uem = args.uem(uri)
    
    # get overlapping speech regions if requested
    if args.no_overlap:
        # make sure timeline is a segmentation
        # tag each resulting segment by all intersecting labels
        tmp_ref = ref >> (ref._timeline.segmentation())
        # overlapping speech regions
        # (ie. timeline made of segments with two tracks or more)
        overlap = pyannote.Timeline([segment for segment in tmp_ref 
                                             if len(tmp_ref[segment, :]) > 1])
    
    # focus on UEM if provided
    if uem is not None:
        # update UEM if overlapping speech regions are removed from evaluation
        # remove overlapping speech regions from UEM if requested
        if args.no_overlap:
            uem = overlap.gaps(focus=uem)
        ref = ref(uem, mode='intersection')
    else:
        # remove overlapping speech regions if requested
        if args.no_overlap:
            ref = ref(overlap.gaps(focus=ref.coverage()), 
                                   mode='intersection')
    
    
    # remove unknown if requested
    if hasattr(args, 'unknown') and args.unknown == 'remove':
        unknows = [label for label in ref.labels() 
                         if isinstance(label, Unknown)]
        ref = ref(unknows, invert=True)
        
    # process each hypothesis file, one after the other
    for h, (path, hypothesis) in enumerate(args.hypothesis):
        
        # read hypothesis for current URI
        hyp = hypothesis(video=uri, modality=ref.modality)
        
        # focus on UEM if provided
        if uem is not None:
            # UEM was already updated to take overlapping speech regions
            # into account -- so no need to worry about that here.
            hyp = hyp(uem, mode='intersection')
        else:
            # remove overlapping speech regions if requested
            if args.no_overlap:
                hyp = hyp(overlap.gaps(focus=hyp.coverage()), 
                                       mode='intersection')
        
        # remove unknown if requested
        if hasattr(args, 'unknown') and args.unknown == 'remove':
            unknows = [label for label in hyp.labels() 
                             if isinstance(label, Unknown)]
            hyp = hyp(unknows, invert=True)
        
        # compute 
        for name, metric in metrics.iteritems():
            details = metric[h](ref, hyp, detailed=True)
            M[name][uri, path] = details[metric[h].name]
            if args.components:
                for component in C[name]:
                    C[name][component][uri, path] = details[component]
        
        pb.update(u*len(args.hypothesis)+h+1)

pb.finish()

AVERAGED = '__ averaged __'
COMBINED = '__ combined __'

# compute averaged & combined metric value
for name, metric in metrics.iteritems():
    for h, (path, _) in enumerate(args.hypothesis):
        M[name][AVERAGED, path] = np.mean(M[name][set(uris), path].M)
        M[name][COMBINED, path] = abs(metric[h])
        if args.components:
            for component in C[name]:
                C[name][component][AVERAGED, path] = \
                                np.mean(C[name][component][set(uris), path].M)
                C[name][component][COMBINED, path] = \
                                np.sum(C[name][component][set(uris), path].M)
            
# if there are more than one hypothesis
# print one table per metric, with one column per hypothesis
if len(args.hypothesis) > 1:
    for name, metric in metrics.iteritems():
        print M[name].to_table(title=name, fmt='1.3', 
                               factorize='C', max_width=10)

# if there is only one hypothesis
# print one single table, with one column per metric
else:
    path, _ = args.hypothesis[0]
    V = LabelMatrix(default=np.inf)
    for name, metric in metrics.iteritems():
        for uri in uris:
            V[uri, name] = M[name][uri, path]
        V[AVERAGED, name] = M[name][AVERAGED, path]
        V[COMBINED, name] = M[name][COMBINED, path]
        if args.components:
            for cname in C[name]:
                for uri in uris:
                    V[uri, '(%s)' % cname] = C[name][cname][uri, path]
                V[AVERAGED, '(%s)' % cname] = C[name][cname][AVERAGED, path]
                V[COMBINED, '(%s)' % cname] = C[name][cname][COMBINED, path]
    print V.to_table(fmt='1.3', factorize='')

if hasattr(args, 'dump'):
    import pickle
    f = open(args.dump, 'w')
    pickle.dump(M, f)
    f.close()
