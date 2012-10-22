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
from pyannote.parser import TimelineParser, LSTParser
from pyannote.parser import MDTMParser
from pyannote.algorithm.clustering.util import LogisticProbabilityMaker
from pyannote.algorithm.clustering.optimization.graph import PreComputedSimilarityGraph, graph2annotation
from pyannote.algorithm.clustering.optimization.gurobi import gurobi2graph, graph2gurobi
from pyannote.algorithm.clustering.optimization.objective import obj_IOP
from gurobipy import GRB

from pyannote.parser.repere.facetracks import FACETRACKSParser
from pyannote.parser.repere.metric import METRICParser

uri_place_holders = ["%s", "[URI]"] 

def replace_placeholders(path, uri):
    new_path = str(path)
    for ph in uri_place_holders:
        new_path = new_path.replace(ph, uri)
    return new_path

argparser = ArgumentParser(description='A tool for face clustering')
argparser.add_argument('--version', action='version', 
                       version=('PyAnnote %s' % pyannote.__version__))

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
    return data['X'], data['Y']


argparser.add_argument('uris', type=uris_parser, 
                       help='path to list used for training')

argparser.add_argument('uem', type=uem_parser, 
                       help='path to Unpartitioned Evaluation Map (UEM) file')

help_msg = "path to .mat file. the following URI placeholders are supported: %s." % " or ".join(uri_place_holders[1:])
argparser.add_argument('metric', type=str, help=help_msg)

help_msg = "path to .facetracks file. the following URI placeholders are supported: %s." % " or ".join(uri_place_holders[1:])
argparser.add_argument('tracks', type=str, help=help_msg)

argparser.add_argument('posterior', type=posterior_parser, metavar='POSTERIOR',
                       help='path to posterior file')

# Next positional argument is output segmentation file
# It is 'w'-opened at argument-parsing time
argparser.add_argument('output', type=output_parser, metavar='OUTPUT',
                        help='path to output of ILP clustering')

argparser.add_argument('--alpha', metavar='ALPHA', type=float, default=0.5,
                       help='ILP coefficient (default: 0.5)')

argparser.add_argument('--prior', metavar='RHO', type=float, default=SUPPRESS,
                       help='Inter/Intra-cluster prior ratio (default: from posterior)')

argparser.add_argument('--verbose', action='store_true',
                       help='print progress information')

# Actual argument parsing
args = argparser.parse_args()

postX, postY  = args.posterior
pm = LogisticProbabilityMaker()

if hasattr(args, 'prior'):
    pm.fit(postX, postY, prior=args.prior)
else:
    pm.fit(postX, postY, prior=None)

preComputedSimilarityGraph = PreComputedSimilarityGraph(cooccurring=True,
                                                        func=pm)

ft_parser = FACETRACKSParser(load_ids=False)
mat_parser = METRICParser(aggregation='average')


# process each URI, one after the other
for u, uri in enumerate(args.uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(args.uris), uri))
        sys.stdout.flush()
    
    # load face tracks
    path = replace_placeholders(args.tracks, uri)
    T = ft_parser.read(path, video=uri)(uri)
    T = T(args.uem(uri), mode='intersection')
    
    # load distance matrix
    path = replace_placeholders(args.metric, uri)
    D = mat_parser.read(path)
    
    g = preComputedSimilarityGraph(T, D)
    
    model, x = graph2gurobi(g)
    model.setParam(GRB.Param.OutputFlag, False)
    model.setParam(GRB.Param.TimeLimit, 20*60)
    model.setParam(GRB.Param.MIPFocus, 1)
    objective, direction = obj_IOP(x, g, alpha=args.alpha)
    model.setObjective(objective, direction)
    model.optimize()
    g = gurobi2graph(model, x)
    output = graph2annotation(g)[uri]['head']
    
    # save to file
    MDTMParser().write(output, f=args.output)

# close output file
args.output.close()