#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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
from progressbar import ProgressBar, Bar, ETA
from pandas import DataFrame, MultiIndex
import numpy as np
import scipy.stats
import networkx as nx
import pyannote
from pyannote.metric.diarization import DiarizationErrorRate, \
                                        DiarizationPurity, \
                                        DiarizationCoverage, \
                                        DiarizationCompleteness, \
                                        DiarizationHomogeneity
from pyannote.metric.detection import DetectionErrorRate
from pyannote.metric.identification import IdentificationErrorRate, \
                                           UnknownIDMatcher

from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.base.matrix import LabelMatrix
from pyannote.base.annotation import Unknown

import pyannote.cli
from argparse import ArgumentParser

def run(args):
    
    # metrics is a dictionary of dictionary
    # metrics[metricName][hypothesisNumber] = metricInstance

    # M is a DataFrame
    # - index: (hypothesis file, uri) pairs
    # - columns: names of metrics and their components

    metrics = {}
    columns = []
    for Metric in args.requested:
        # get metric name
        metricName = Metric.metric_name()
        # instantiate one metric per hypothesis
        if Metric == IdentificationErrorRate:
            metrics[metricName] = {h: Metric(matcher=UnknownIDMatcher()) 
                                   for h,(_,_) in enumerate(args.hypothesis)}
        else:
            metrics[metricName] = {h: Metric() for h,(_,_) in enumerate(args.hypothesis)}
            
        # add metric name
        columns.append(metricName)
        columns.extend(['%s | %s' % (metricName, componentName) 
                        for componentName in Metric.metric_components()])

    index = MultiIndex(levels=[[],[]], labels=[[],[]], names=['hypothesis', 'uri'])
    M = DataFrame(index=index, columns=columns)

    # Obtain final list of URIs to process 
    # (either from --uri(s) options or from input files)
    uris = pyannote.cli.URIHandler().uris()

    pb = ProgressBar(widgets=[Bar(),' ', ETA()], term_width=80)
    pb.maxval = len(uris)*len(args.hypothesis)
    pb.start()

    if hasattr(args, 'modality'):
        modality = args.modality
    else:
        modality = None

    # process each URI, one after the other
    for u, uri in enumerate(uris):
    
        # read reference for current URI
        ref = args.groundtruth(uri=uri, modality=modality)
    
        # read UEM if provided
        if hasattr(args, 'uem'):
            uem = args.uem(uri)
        else:
            uem = None
    
        # get overlapping speech regions if requested
        if args.no_overlap:
            # make sure timeline is a segmentation
            # tag each resulting segment by all intersecting labels
            tmp_ref = ref >> (ref.timeline.segmentation())
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
            ref = ref.crop(uem, mode='intersection')
        else:
            # remove overlapping speech regions if requested
            if args.no_overlap:
                ref = ref.crop(overlap.gaps(focus=ref.coverage()), 
                               mode='intersection')
    
        # process each hypothesis file, one after the other
        for h, (path, hypothesis) in enumerate(args.hypothesis):
        
            # read hypothesis for current URI
            # hyp = hypothesis(uri=uri, modality=ref.modality)
            hyp = hypothesis(uri, modality)
        
            # focus on UEM if provided
            if uem is not None:
                # UEM was already updated to take overlapping speech regions
                # into account -- so no need to worry about that here.
                hyp = hyp.crop(uem, mode='intersection')
            else:
                # remove overlapping speech regions if requested
                if args.no_overlap:
                    hyp = hyp.crop(overlap.gaps(focus=hyp.coverage()), 
                                   mode='intersection')
        
            # compute 
            for metricName, metric in metrics.iteritems():
                details = metric[h](ref, hyp, detailed=True)
                # M[name][uri, path] = details[metric[h].name]
                for componentName, value in details.iteritems(): 
                    if componentName == metricName:
                        M = M.set_value((path, uri), metricName, value)
                    else:
                        M = M.set_value((path, uri), 
                                        '%s | %s' % (metricName, componentName),
                                        value)
        
            pb.update(u*len(args.hypothesis)+h+1)

    pb.finish()

    # compute global (ie. combined) metric value
    for metricName, metric in metrics.iteritems():
        for h, (path, _) in enumerate(args.hypothesis):
            M = M.set_value((path, '/all'), metricName, abs(metric[h]))

    M.to_csv(args.dump, index_label=['hypothesis', 'uri'], header=True, index=True)
    args.dump.close()


def view(args):
    
    M = DataFrame.from_csv(args.input, index_col=[0,1])
    
    hypotheses = list(M.index.levels[0])
    uris = list(M.index.levels[1])
    if '/all' in uris:
        uris.remove('/all')
    
    if args.list:
        
        if 'M' in args.list:
            print "Metrics"
            print "======="
            for column in M:
                print column
        
        if 'H' in args.list:
            print "Hypotheses"
            print "=========="
            for hyp in hypotheses:
                print hyp
        
        if 'U' in args.list:
            print "URIS"
            print "===="
            for uri in uris:
                print uri
        
        exit(1)
    
    # focus on requested metric
    if not args.metric:
        exit('ERROR: missing --metric name.')
    
    metricName = args.metric
    m = M[metricName]
    
    # get scores for all hypothesis/resource
    runs = [(path, m[path][uris]) for path in hypotheses]
    
    combined = {path: m[path]['/all'] for path in hypotheses}
    averaged = {path: np.mean(run) for path,run in runs}
    geometric = {path: scipy.stats.gmean(run) for path,run in runs}
    harmonic = {path: scipy.stats.hmean(run) for path,run in runs}
    medianed = {path: np.median(run) for path,run in runs}
    
    if args.aggregate == 'combine':
        aggregated = combined
    elif args.aggregate == 'average':
        aggregated = averaged
    elif args.aggregate == 'median':
        aggregated = medianed
    elif args.aggregate == 'geometric':
        aggregated = geometric
    elif args.aggregate == 'harmonic':
        aggregated = harmonic
    
    # perform statistical significance tests on metric values
    # create a directed graph with one vertex per hypothesis file
    # directed edges mean source is significantly better than target 
    G = nx.DiGraph(name=metricName)
    for r, (path,run) in enumerate(runs):
        value = aggregated[path]
        G.add_node(path, **{metricName: value})
        for (other_path,other_run) in runs[r+1:]:
            other_value = aggregated[other_path]
            _,p = scipy.stats.wilcoxon(run, other_run)
            if p < 0.05:
                if value < other_value:
                    G.add_edge(path, other_path, wilcoxon=p)
                else:
                    G.add_edge(other_path, path, wilcoxon=p)
    
    nx.write_gpickle(G, '/tmp/significance.nxg')
    
    # sort runs based on how many times they are significantly better
    # than other runs
    D = max([d for _,d in G.out_degree_iter()])
    best = sorted([(p, G.node[p][metricName]) for p,d in G.out_degree_iter() 
                                              if d == D],
                  key=lambda t:t[1], reverse=True)
    
    if args.significance:
        print "Statistically best runs"
        print "======================="
        for p,v in best:
            print "%s : %.3f" % (p,v)
        
        exit(1)
    
    ordered = [(p,v) for p,v in aggregated.iteritems()]
    ordered = sorted(ordered, key=lambda t:t[1])
    print "%d best runs" % args.best
    print "=============="
    for k, (p,v) in enumerate(ordered):
        if k < args.best:
            print "%s : %.3f" % (p,v)
    
    


argparser = ArgumentParser('pyeval.py')

subparsers = argparser.add_subparsers(title='Switch between "run" and "view" modes', 
                                      help='use "run" mode to perform evaluation. '
                                           'use "view" mode to visualize results.')

runparser = subparsers.add_parser('run', 
                                  parents=[pyannote.cli.parent.parentArgumentParser()],
                                  description='"run" mode allows to generate evaluation file.')
runparser.set_defaults(func=run)

description = 'path to reference.' + pyannote.cli.URI_SUPPORT
runparser.add_argument('groundtruth', metavar='reference',
                       type=pyannote.cli.InputGetAnnotation(),
                       help=description)

description = 'path to hypothesis.' + pyannote.cli.URI_SUPPORT
runparser.add_argument('hypothesis', metavar='hypothesis', nargs='+',
                       type=pyannote.cli.InputGetAnnotationAndPath(), 
                       help=description)

description = 'path to output file. Use "-" for stdout.'
runparser.add_argument('dump', metavar='output.csv',
                       type=pyannote.cli.OutputFileHandle(), 
                       help=description)

description = 'remove overlap regions (in reference) from evaluation map.'
runparser.add_argument('--no-overlap', action='store_true', help=description)

description = 'print value of error rate components.'
runparser.add_argument('--components', action='store_true', help=description)

description = 'choose evaluated modality in case reference contains several.'
runparser.add_argument('--modality', metavar='MODALITY', type=str, 
                       default=pyannote.cli.SUPPRESS, help=description)

group = runparser.add_argument_group('Diarization & clustering')

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

group = runparser.add_argument_group('Detection')

description = 'compute detection error rate'
group.add_argument('--detection', action='append_const', dest='requested',
                                    const=DetectionErrorRate, default=[],
                                    help=description)

group = runparser.add_argument_group('Identification')

description = 'compute identification error rate'
group.add_argument('--identification', action='append_const', dest='requested',
                                       const=IdentificationErrorRate, default=[],
                                       help=description)

viewparser = subparsers.add_parser('view', 
                                  parents=[pyannote.cli.parent.parentArgumentParser(uem=False, uri=False)],
                                  description='"view" mode allows to visualize evaluation file.')
viewparser.set_defaults(func=view)

description = 'path to evaluation file. Use "-" for stdin.'
viewparser.add_argument('input', metavar='evaluation.csv',
                       type=pyannote.cli.InputFileHandle(), 
                       help=description)

description = 'list file content (M: metrics, H: hypotheses, U: URIs)'
viewparser.add_argument('--list', action='append', choices=('M', 'H', 'U'),
                        default=[], help=description)

description = 'select evaluation metric. use --list M to know which are available.'
viewparser.add_argument('--metric', type=str, help=description)

description = 'select how metric values are aggregated.'
viewparser.add_argument('--aggregate', default='combine',
                        choices=('combine', 'average', 'median', 'geometric', 'harmonic'),
                        help=description)

description = 'display output of Wilcoxon significance test'
viewparser.add_argument('--significance', action='store_true', help=description)

description = 'display only N best runs (default to 10)'
viewparser.add_argument('--best', type=int, default=10, help=description)

# Actual argument parsing
try:
    args = argparser.parse_args()
except Exception, e:
    sys.exit(e)

args.func(args)

