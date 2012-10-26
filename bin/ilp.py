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
import networkx as nx
from argparse import ArgumentParser, SUPPRESS
from pyannote.parser import AnnotationParser, TimelineParser, LSTParser, PLPParser, MDTMParser
from pyannote.base.matrix import LabelMatrix
from pyannote.algorithm.clustering.optimization.graph import LabelSimilarityGraph, LabelCooccurrenceGraph, LabelIdentityGraph
from pyannote.algorithm.clustering.optimization.gurobi import GurobiModel

import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='A tool for multimodal ILP clustering')

def src_parser(path):
    return AnnotationParser().read(path)
argparser.add_argument('src', type=src_parser, nargs='+', 
                       help='path to source annotation (one per modality)')

def out_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
argparser.add_argument('output', type=out_parser, metavar='output.mdtm',
                       help='path to where to store output in MDTM format')

argparser.add_argument('--time-limit', type=int, metavar='n_min', 
                       default=SUPPRESS,
                       help='force stop if ILP optimization has not converged '
                            'to the optimal solution after n_min minutes')

argparser.add_argument('--alpha', type=float, metavar='α', 
                       default=0.5,
                       help='set α in objective function. '
                            'smaller α means bigger clusters.')

def speaker_parser(path):
    
    f = open(path, 'r')
    data = pickle.load(f)
    f.close()
    
    mmx = data.pop('MMx')
    class SSGraph(LabelSimilarityGraph, mmx):
        def __init__(self):
            super(SSGraph, self).__init__(**data)
    
    ssGraph = SSGraph()
    
    return ssGraph

sparser = argparser.add_argument_group("[speaker] modality")
sparser.add_argument('--speaker', type=speaker_parser, 
                     metavar='params.pkl', default=SUPPRESS, 
                     help='path to trained parameters for speaker/speaker '
                          'similarity graph')

msg = "path to PLP feature files. " \
      "URI placeholders are supported: %s." % " or ".join(clicommon.URIS[1:])
sparser.add_argument('--plp', type=str, metavar='file.plp', help=msg)


wparser = argparser.add_argument_group("[written] modality")
wparser.add_argument('--written', action='store_true', default=SUPPRESS,
                     help="incorporate the [written] modality")

def cross_parser(path):
    
    f = open(path, 'r')
    data = pickle.load(f)
    f.close()
    
    crossGraph = LabelCooccurrenceGraph(**data)
    
    return crossGraph

xparser = argparser.add_argument_group("Cross-modality")
xparser.add_argument('--cross', type=cross_parser, action='append',
                     dest='cross', default=[], metavar='params.pkl',
                     help='path to trained parameters for cross-modal graphs')

try:
   args = argparser.parse_args()
except IOError as e:
   sys.stderr.write('%s' % e)
   sys.exit(-1)


# get list of modalities & resources from sources
modalities = {}
uris = set([])
for src in args.src:
    for m in src.modalities:
        if m not in modalities:
            modalities[m] = []
        modalities[m].append(src)
        uris.update(set(src.videos))

# if list of resources is provided, use it.
if hasattr(args, 'uris'):
    uris = args.uris
else:
    uris = sorted(uris)

# make sure there is at most one source per modality
for m in modalities:
    if len(modalities[m]) > 1:
        msg = "ERROR: found more than one source for modality [%s].\n" % m
        sys.stderr.write(msg)
        sys.exit(-1)
for m in set(modalities):
    modalities[m] = modalities[m][0]

# make sure incorporated modalities are available
for m in ['speaker', 'written', 'head', 'spoken']:
    if hasattr(args, m) and m not in modalities:
        msg = "ERROR: could not find any source for modality [%s].\n" % m


# make sure modalities for cross-modal graphs are available
for c in args.cross:
    for m in [c.modalityA, c.modalityB]:
        if m not in modalities:
            msg = "ERROR: could not find any source for modality [%s].\n" % m
            sys.stderr.write(msg)
            sys.exit(-1)

for u, uri in enumerate(uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    # start with an empty graph
    G = nx.Graph()
    
    if hasattr(args, 'uem'):
        uem = args.uem(uri)
    else:
        uem = None
    
    # add speaker similarity graph
    if hasattr(args, 'speaker'):
        
        if args.verbose:
            sys.stdout.write('   - [speaker/speaker] similarity graph\n')
            sys.stdout.flush()
        
        # load PLP features
        path = clicommon.replaceURIS(args.plp, uri)
        plp = PLPParser().read(path)
        
        # get source
        src = modalities['speaker'](video=uri, modality='speaker')
        if uem is not None:
            src = src(uem, mode='intersection')
        
        # create speaker similarity graph
        g = args.speaker(src, plp)
        
        # add it to 'big graph'
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
        
    # add written identity graph
    if hasattr(args, 'written'):
        
        if args.verbose:
            sys.stdout.write('   - [written] identity graph\n')
            sys.stdout.flush()
        
        # get source
        src = modalities['written'](video=uri, modality='written')
        if uem is not None:
            src = src(uem, mode='intersection')
        
        # create written identity graph
        g = LabelIdentityGraph()(src)
        
        # add it to 'big graph'
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # add cross-modal graphs
    for c in args.cross:
        
        # get sources
        modA = c.modalityA
        srcA = modalities[modA](video=uri, modality=modA)
        if uem is not None:
            srcA = srcA(uem, mode='intersection')
        
        modB = c.modalityB
        srcB = modalities[modB](video=uri, modality=modB)
        if uem is not None:
            srcB = srcB(uem, mode='intersection')
        
        if args.verbose:
            sys.stdout.write('   - [%s/%s] cross-modal graph\n' % (modA, modB))
            sys.stdout.flush()
        
        # create cross-modal graph
        g = c(srcA, srcB)
        
        # add it to 'big graph'
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    
    # create ILP model
    if hasattr(args, "time_limit"):
        timeLimit = args.time_limit * 60
    else:
        timeLimit = None
    model = GurobiModel(G, timeLimit=timeLimit, threads=None, 
                           quiet=len(args.verbose) < 2)
    
    # set objective
    model.setObjective(alpha=args.alpha)
    
    # optimize 
    model.optimize()
    
    for m in modalities:
        # reconstruct
        src = modalities[m](video=uri, modality=m)
        output = model.reconstruct(src)
        # save to file
        MDTMParser().write(output, f=args.output)

args.output.close()
