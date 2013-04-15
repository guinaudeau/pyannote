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

# =============================================================================
# IMPORTS
# =============================================================================
import sys
import pyannote.cli  # common PyAnnote Command Line Interface
import networkx as nx  # graph handling
import numpy as np

from pyannote.algorithm.mpg.util import densify
from pyannote.algorithm.mpg.node import IdentityNode, TrackNode
from pyannote.algorithm.mpg.graph import PROBABILITY
from pyannote.base.annotation import Annotation, Unknown

from pyannote.algorithm.mpg.gurobi2 import ILPClusteringMixin, FinkelConstraintMixin, INTRAinterObjectiveMixin

# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================
argParser = pyannote.cli.initParser('Clustering of Multimodal Probability Graphs', uem=False)

description = 'path to input file (pickled Networkx graph).' + pyannote.cli.URI_SUPPORT
argParser.add_argument('input', help=description,
                       type=pyannote.cli.InputFileHandle())

description = 'path to output annotation.' + pyannote.cli.URI_SUPPORT
argParser.add_argument('output', help=description,
                       type=pyannote.cli.OutputWriteAnnotation())

description = 'dump Gurobi model to file (one per sub-problem).' + pyannote.cli.URI_SUPPORT
argParser.add_argument('--dump', metavar='model.%02d.mps', help=description,
                       type=str, default=pyannote.cli.SUPPRESS)

description = 'densify graph before optimization.'
argParser.add_argument('--densify', action='store_true', help=description)

description = 'set value of alpha (default is 0.5).'
argParser.add_argument('--alpha', type=float, default=0.5, help=description)

description = 'apply connected components pruning before optimization'
argParser.add_argument('--pruning', action='store_true', help=description)

description = 'select objective function. Not supported yet.'
argParser.add_argument('--objective', type=int, default=1, help=description)

# 1 : Maximize ∑ α.xij.pij + (1-α).(1-xij).(1-pij)
# 2 : Maximize ∑ α.wij.xij.pij + (1-α).wij.(1-xij).(1-pij)
# 3 : Maximize modularity'
# 4 : Maximize ∑ α.xij.log(pij) + (1-α).(1-xij).log(1-pij)
# 5 : Minimize ∑ xii + ∑ ∑ (1-pij).xij')

description = 'set duration-weighting strategy. Not supported yet.'
argParser.add_argument('--weight', choices=('none', 'min', 'max', 'avg'),
                       default='none', help=description)

argGurobi = argParser.add_argument_group('Gurobi parameters')

description = ('set optimization method: primal (0), dual (1), barrier (2), '
               'concurrent (3, default) or determinisic (4).')
argGurobi.add_argument('--method', type=int, default=3, help=description)

description = ('set high-level strategy: find feasible solutions (1), '
               'prove optimality (2), focus on the bound (3). Default (0) is '
               'to balance between 1 and 2.')
argGurobi.add_argument('--mip-focus', type=int, default=0, help=description)

description = ('set the amount of time spent in MIP heuristics. Default is 5%%.')
argGurobi.add_argument('--heuristics', type=float, default=0.05, help=description)

description = ('stop optimization when the relative gap between the lower and '
               'upper objective bound is less than X times the upper bound. '
               'Default is 1e-4.')
argGurobi.add_argument('--mip-gap', type=float, default=1e-4,
                       metavar='X', help=description)

description = 'stop optimization after N hours.'
argGurobi.add_argument('--time-limit', metavar='N', type=float,
                       default=1e100/3600, help=description)

description = ('set the number of threads to parallel MIP.')
argGurobi.add_argument('--threads', type=int, default=0, help=description)

# =============================================================================
# ARGUMENT PARSING & POST-PROCESSING
# =============================================================================
try:
    args = argParser.parse_args()
except IOError as e:
    sys.stderr.write('%s' % e)
    sys.exit(-1)

# obtain list of resources
uris = pyannote.cli.get_uris()

# Finkel or Dupuy?
if args.objective == 1:
    constraintMixin = FinkelConstraintMixin
    objectiveMixin = INTRAinterObjectiveMixin
else:
    constraintMixin = FinkelConstraintMixin
    objectiveMixin = INTRAinterObjectiveMixin


class MyILP(ILPClusteringMixin, constraintMixin, objectiveMixin):
    pass


def get_similarity(I, J, g):
    if g.has_edge(I, J):
        return g[I][J][PROBABILITY]
    else:
        return np.nan

debug = len(args.verbose) > 2

# =============================================================================
# PROCESSING ONE RESOURCE AT A TIME
# =============================================================================
for u, uri in enumerate(uris):

    # inform the user about which resource is being processed
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()

    # pickle multimodal probability graph
    with args.input(uri=uri) as f:
        G = nx.read_gpickle(f)

    if args.densify:
        G = densify(G, copy=False)

    # process each connected components subgraph separately
    threshold = (1.-args.alpha) if args.pruning else 0.
    for i, g in enumerate(G.subgraphs_iter(threshold=threshold)):

        # initialize ILP problem
        problem = MyILP(g.nodes(), g, get_similarity=get_similarity,
                        alpha=args.alpha, debug=debug)

        # dump ILP problem to file
        if hasattr(args, 'dump'):
            problem.dump(args.dump % i)

        # solve ILP problem
        clusters = problem.solve(method=args.method,
                                 mip_focus=args.mip_focus,
                                 heuristics=args.heuristics,
                                 mip_gap=args.mip_gap,
                                 time_limit=3600*args.time_limit,
                                 threads=args.threads,
                                 verbose=len(args.verbose) > 1)

        for cluster in clusters:

            # find identity in cluster
            identities = set([i.identifier for i in cluster
                              if isinstance(i, IdentityNode)])
            try:
                identity = identities.pop()
            except Exception, e:
                identity = Unknown()

            # find list of modalities in cluster
            modalities = set([t.modality for t in cluster
                              if isinstance(t, TrackNode)])

            # create one annotation per modality
            for modality in modalities:
                annotation = Annotation(uri=uri, modality=modality)
                for t in cluster:
                    if isinstance(t, TrackNode) and t.modality == modality:
                        annotation[t.segment, t.track] = identity
                args.output(annotation)
