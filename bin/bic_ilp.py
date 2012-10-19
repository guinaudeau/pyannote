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

import os
import socket
os.putenv('GRB_LICENSE_FILE', "%s/licenses/%s.lic" % (os.getenv('GUROBI_HOME'),
                                                      socket.gethostname()))

import sys
import pickle
import pyannote
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser
from pyannote.parser import PLPParser, MDTMParser
from pyannote.algorithm.clustering.util import LogisticProbabilityMaker
from pyannote.algorithm.clustering.model.base import SimilarityMatrix
from pyannote.algorithm.clustering.model.gaussian import BICMMx
from pyannote.algorithm.clustering.optimization.graph import SimilarityGraph, graph2annotation
from pyannote.algorithm.clustering.optimization.gurobi import gurobi2graph, graph2gurobi
from pyannote.algorithm.clustering.optimization.objective import obj_IOP
from gurobipy import GRB

place_holders = ["%s", "[URI]"] 

argparser = ArgumentParser(description='A tool for BIC clustering')
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
def posterior_parser(path):
    f = open(path, 'r')
    data = pickle.load(f)
    f.close()
    return data['X'], data['Y'], data['penalty_coef'], data['covariance_type']

# First positional argument is input segmentation file
# It is loaded at argument-parsing time by an instance of AnnotationParser
argparser.add_argument('input', type=input_parser, metavar='INPUT',
                       help='path to input segmentation file')

help_msg = "path to PLP feature file. the following URI placeholders are supported: %s." % " or ".join(place_holders[1:])
argparser.add_argument('plp', metavar='PLP', type=str, 
                       help=help_msg)

argparser.add_argument('posterior', type=posterior_parser, metavar='POSTERIOR',
                       help='path to posterior file')

# Next positional argument is output segmentation file
# It is 'w'-opened at argument-parsing time
argparser.add_argument('output', type=output_parser, metavar='OUTPUT',
                        help='path to output of BIC/ILP clustering')

argparser.add_argument('--uris', type=uris_parser,
                       help='list of URI to process')

# UEM file is loaded at argument-parsing time by an instance of TimelineParser
argparser.add_argument('--uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM) file')

argparser.add_argument('--alpha', metavar='ALPHA', type=float, default=0.5,
                       help='ILP coefficient (default: 0.5)')

argparser.add_argument('--prior', metavar='RHO', type=float, default=SUPPRESS,
                       help='Inter/Intra-cluster prior ratio (default: from posterior)')

argparser.add_argument('--verbose', action='store_true',
                       help='print progress information')

# Actual argument parsing
args = argparser.parse_args()


postX, postY, penalty_coef, covariance_type = args.posterior
pm_bic = LogisticProbabilityMaker()
if hasattr(args, 'prior'):
    pm_bic.fit(postX, postY, prior=args.prior)
else:
    pm_bic.fit(postX, postY, prior=None)

class BICSimilarityGraph(SimilarityGraph, BICMMx):
    def __init__(self):
        super(BICSimilarityGraph, self).__init__(
                            covariance_type=covariance_type,
                            penalty_coef=penalty_coef,
                            func=pm_bic)

bicSimilarityGraph = BICSimilarityGraph()

# only process selection of uris
if args.uris:
    uris = args.uris
else:
    uris = args.input.videos

# process each URI, one after the other
for u, uri in enumerate(uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    # input annotation
    annotation = args.input(uri)
    annotation.modality = 'speaker'
    
    # focus on UEM
    if args.uem is not None:
        uem = args.uem(uri)
        annotation = annotation(uem, mode='intersection')
    
    # PLP features
    path = args.plp
    for ph in place_holders:
        path = path.replace(ph, uri)
    feature = PLPParser().read(path)
    
    g = bicSimilarityGraph(annotation, feature)
    model, x = graph2gurobi(g)
    model.setParam(GRB.Param.OutputFlag, False)
    model.setParam(GRB.Param.TimeLimit, 20*60)
    model.setParam(GRB.Param.MIPFocus, 1)
    objective, direction = obj_IOP(x, g, alpha=args.alpha)
    model.setObjective(objective, direction)
    model.optimize()
    g = gurobi2graph(model, x)
    output = graph2annotation(g)[uri]['speaker']
    
    # save to file
    MDTMParser().write(output, f=args.output)

# close output file
args.output.close()