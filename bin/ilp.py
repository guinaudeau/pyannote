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

argparser = ArgumentParser(parents=[clicommon.parser],
                           description='Multimodal Prob Graph ILP clustering')

def input_parser(path):
    
    def load_mpg(uri):
        return nx.read_gpickle(clicommon.replaceURI(path, uri))
    
    return load_mpg
    
msg = 'path to input Multimodal Probability Graph. ' + clicommon.msgURI()
argparser.add_argument('input', type=input_parser, metavar='mpg.pkl', help=msg)

def output_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
argparser.add_argument('output', type=output_parser, metavar='output.mdtm',
                       help='path to where to store output in MDTM format')

group = argparser.add_argument_group('Objective function')

group.add_argument('--objective', choices = ('finkel', ), default='finkel',
                   help='choose objective function.')
group.add_argument('--alpha', type=float, metavar='ALPHA', default=0.5,
                   help='set α value to ALPHA in objective function.')
group.add_argument('--log-prob', action='store_true', 
                   help='use log probability instead of probability.')

ogroup = argparser.add_argument_group('Optimization')

def method_parser(method):
    return {'primal': 0, 'dual': 1, 'barrier': 2,
            'concurrent': 3, 'deterministic': 4}[method]

ogroup.add_argument('--method', default='primal', type=str,
                    choices = ('primal', 'dual', 'barrier', 'concurrent',
                                                            'deterministic'),
                    help="set algorithm used to solve the root node of the MIP "
                         "model: primal simplex (default), dual simplex, "
                         "barrier, concurrent or deterministic concurrent.")
ogroup.add_argument('--mip-gap', type=float, metavar='MIPGAP', default=1e-4,
                    help='The MIP solver will terminate when the relative gap '
                         'between the lower and upper objective bound is less '
                         'than MIPGAP times the upper bound.')
ogroup.add_argument('--stop-after', type=int, metavar='N', default=SUPPRESS,
                       help='stop optimization after N minutes')
# ogroup.add_argument('--maxnodes', type=int, metavar='N', default=SUPPRESS,
#                     help='do not try to perform optimization if number of '
#                          'is higher than N.')
ogroup.add_argument('--threads', type=int, metavar='N', default=SUPPRESS, 
                    help='number of threads to use.')

# ogroup.add_argument('--prune-mm', type=float, metavar='P', default=0.0,
#                     help='set probability of mono-modal edges to zero '
#                          'in case it is already lower than P.')

dgroup = argparser.add_argument_group('Debugging')

def dump_model_parser(model_mps):
    def dump(model, uri):
        path = clicommon.replaceURI(model_mps, uri)
        model.model.update()
        model.model.write(path)
    return dump

# msg = "dump meta-graph before optimization." + clicommon.msgURI()
# dgroup.add_argument('--dump-graph', type=dump_graph_parser,
#                     metavar='graph.pkl', help=msg, default=SUPPRESS)

msg = "dump model before optimization." + clicommon.msgURI()
dgroup.add_argument('--dump-model', type=dump_model_parser,
                    metavar='model.mps', help=msg, default=SUPPRESS)

try:
    args = argparser.parse_args()
except IOError as e:
    sys.exit(e)

if not hasattr(args, 'uris'):
    raise IOError('missing list of resources (--uris)')

from pyannote.algorithm.clustering.optimization.graph import IdentityNode, TrackNode, meta_mpg
from pyannote.algorithm.clustering.optimization.gurobi import GurobiModel
from pyannote.parser import MDTMParser
from pyannote.base.annotation import Annotation, Unknown
import time

def reconstruct(clusters, uri, modality):
    
    A = Annotation(uri=uri, modality=modality)
    
    for cluster in clusters:
        
        # obtain cluster identity
        inodes = set([n for n in cluster if isinstance(n, IdentityNode)])
        if len(inodes) == 1:
            label = inodes.pop().identifier
        else:
            label = Unknown()
        
        tnodes = set([n for n in cluster 
                        if isinstance(n, TrackNode) and n.modality == modality])
        
        tracks = {}
        for n in tnodes:
            if n.track not in tracks:
                tracks[n.track] = n.segment
            else:
                tracks[n.track] = tracks[n.track] | n.segment 
        
        for track in tracks:
            A[tracks[track], track] = label
    
    return A


for u, uri in enumerate(args.uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(args.uris), uri))
        sys.stdout.flush()
    
    # load Multimodal Probability Graph
    mpg = args.input(uri)
    
    # obtain list of modalities contained in the MPG
    modalities = set([n.modality 
                      for n in mpg if not isinstance(n, IdentityNode)])
    
    # get meta-MPG (create one meta-node for nodes connected with prob=1)
    mmpg, meta_nodes = meta_mpg(mpg)
    
    # # pruning
    # for e,f,data in G.edges(data=True):
    #     
    #     # label/label pruning
    #     if isinstance(e, LabelNode) and isinstance(f, LabelNode):
    #         # mono-modal label/label pruning
    #         if e.modality == f.modality:
    #             if data[PROBABILITY] < args.prune_mm:
    #                 # keep track of pruning info
    #                 # only for debugging purpose
    #                 if hasattr(args, 'dump_graph'):
    #                     G[e][f]['pruned'] = True
    #                 G[e][f][PROBABILITY] = 0.
    #         # cross-modal label/label pruning
    #         else:
    #             pass
    
    if hasattr(args, 'maxnodes') and len(mmpg) > args.maxnodes:
        
        status_msg = 'Too many nodes (%d > %d).' % (len(mmpg), args.maxnodes)
        model_time = 0
        optimization_time = 0
        
        # reconstruct from existing meta_nodes
        clusters = meta_nodes
    
    else:
        
        # actual optimization
        if hasattr(args, 'stop_after'):
            stopAfter = args.stop_after * 60
        else:
            stopAfter = None
        
        if hasattr(args, 'threads'):
            threads = args.threads
        else:
            threads = None
        
        # create Gurobi model
        start_time = time.time()
        model = GurobiModel(mmpg, method=method_parser(args.method),
                                      mipGap=args.mip_gap,
                                      threads=threads,
                                      timeLimit=stopAfter, 
                                      quiet=len(args.verbose) < 2)
        model_time = time.time() - start_time
        
        model.setObjective(type=args.objective,
                           alpha=args.alpha,
                           log_prob=args.log_prob)
        
        # dump model
        if hasattr(args, 'dump_model'):
            args.dump_model(model, uri)
        
        # optimization
        start_time = time.time()
        CC, status_num, status_msg = model.optimize()
        optimization_time = time.time() - start_time

        # concatenate every meta-nodes from each cluster
        clusters = [list() for cc in CC]
        for c, cc in enumerate(CC):
            for meta_node in cc:
                clusters[c].extend(meta_nodes[meta_node])
        
        del model

    annotations = {modality: reconstruct(clusters, uri=uri, modality=modality) for modality in modalities}
    
    MDTMParser().comment(uri, f=args.output)
    MDTMParser().comment(status_msg, f=args.output)
    msg = 'Model took %ds to create and %ds to optimize.\n' % \
                                                        (int(model_time), 
                                                         int(optimization_time))
    MDTMParser().comment(msg, f=args.output)
    
    for modality in annotations:
        MDTMParser().write(annotations[modality], f=args.output)
    
args.output.close()
    
