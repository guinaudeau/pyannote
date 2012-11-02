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

# from pyannote.parser import AnnotationParser, TimelineParser, LSTParser, PLPParser, MDTMParser
# from pyannote.base.matrix import LabelMatrix
# from pyannote.algorithm.clustering.optimization.gurobi import GurobiModel

from argparse import ArgumentParser, SUPPRESS
from pyannote import clicommon

argparser = ArgumentParser(parents=[clicommon.parser],
                           description='A tool for multimodal ILP clustering')

from pyannote.parser import AnnotationParser
def mm_parser(path):
    """Speaker diarization & face clustering source annotation
    
    Parameters
    ----------
    path : str
        Path to source annotation (may contain [URI] placeholder)
    
    Returns
    -------
    annotation_generator : func or AnnotationParser
        callable (e.g. annotation_generator(uri)) object 
        that returns the annotation for a given resource.
    
    """
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
                         .read(clicommon.replaceURI(path, u), video=u)(u)
    else:
        return AnnotationParser().read(path)

from pyannote.algorithm.clustering.optimization.graph import LabelSimilarityGraph
def ss_param_parser(param_pkl):
    """Speaker diarization
    
    Parameters
    ----------
    param_pkl : str
        Path to 'param.pkl' parameter file.
        
    Returns
    -------
    graph_generator : LabelSimilarityGraph
        callable (e.g. graph_generator(annotation, feature)) object 
        that returns a label similarity graph
    """
    
    with open(param_pkl, 'r') as f:
        params = pickle.load(f)
    
    mmx = params.pop('__mmx__')
    func = params.pop('__s2p__')
    
    class SSGraph(LabelSimilarityGraph, mmx):
        def __init__(self):
            super(SSGraph, self).__init__(func=func, **params)
    
    graph_generator = SSGraph()
    
    return graph_generator

from pyannote.parser import PLPParser
def ss_plp_parser(path):
    """PLP feature loader
    
    Parameters
    ----------
    path : str
        Path to PLP feature file (with [URI] placeholder)
    
    Returns
    -------
    load_plp : func
        function that takes uri as unique argument and returns PLP features
    
    """
    def load_plp(uri):
        return PLPParser().read(clicommon.replaceURI(path, uri))
    
    return load_plp

from pyannote.algorithm.clustering.optimization.graph import LabelIdentityGraph
def si_parser(path):
    raise NotImplementedError('--si option is not supported yet.')

def si_param_parser(path):
    raise NotImplementedError('--si-param option is not supported yet.')

from pyannote.algorithm.clustering.model import PrecomputedMMx
def hh_param_parser(param_pkl):
    """Face clustering
    
    Parameters
    ----------
    param_pkl : str or None
        Path to 'param.pkl' parameter file.
        
    Returns
    -------
    graph_generator : LabelSimilarityGraph
        callable (e.g. graph_generator(annotation, feature)) object 
        that returns a label similarity graph
    """
    
    if param_pkl is None:
        class HHGraph(LabelSimilarityGraph, PrecomputedMMx):
            def __init__(self):
                super(HHGraph, self).__init__()
        
        graph_generator = HHGraph()
    else:
        with open(param_pkl, 'r') as f:
            params = pickle.load(f)
    
        mmx = params.pop('__mmx__')
        func = params.pop('__s2p__')
    
        class HHGraph(LabelSimilarityGraph, mmx):
            def __init__(self):
                super(HHGraph, self).__init__(func=func, **params)
    
        graph_generator = HHGraph()
    
    return graph_generator


from pyannote.parser import LabelMatrixParser
def hh_precomputed_parser(path):
    """Precomputed similarity matrix loader
    
    Parameters
    ----------
    path : str
        Path to precomputed matrices (with [URI] placeholder)
    
    Returns
    -------
    load_matrix : func
        function that takes uri as unique argument and returns matrix
    
    """
    
    def load_matrix(uri):
        return LabelMatrixParser().read(clicommon.replaceURI(path, uri))
    
    return load_matrix
    
def hi_parser(path):
    raise NotImplementedError('--hi option is not supported yet.')

def hi_param_parser(path):
    raise NotImplementedError('--hi-param option is not supported yet.')

def wi_parser(path):
    """Written name detection source
    
    Parameters
    ----------
    path : str
        Path to written name detection source
    
    Returns
    -------
    annotation_generator : AnnotationParser
        callable (e.g. annotation_generator(uri)) object
        that returns the annotation for a given resource
    
    """
    return AnnotationParser().read(path)

def wi_param_parser(path):
    if path is None:
        graph_generator = LabelIdentityGraph()
    else:
        raise NotImplementedError('--wi-param option is not supported yet.')
    return graph_generator
    
    
def ni_parser(path):
    raise NotImplementedError('--ni option is not supported yet.')

def ni_param_parser(path):
    raise NotImplementedError('--ni-param option is not supported yet.')

from pyannote.algorithm.clustering.optimization.graph import LabelCooccurrenceGraph
def x_param_parser(param_pkl):
    """Cross-modal graph
    
    Parameters
    ----------
    param_pkl : str
        Path to 'param.pkl' parameter file
    
    Returns
    -------
    graph_generator : LabelCooccurrenceGraph
        callable (e.g. graph_generator(speaker, head)) object 
        that returns a label cooccurrence graph
    
    """
    with open(param_pkl, 'r') as f:
        params = pickle.load(f)
    
    graph_generator = LabelCooccurrenceGraph(**params)
    
    def xgraph(src1, src2):
        modA = graph_generator.modalityA
        modB = graph_generator.modalityB
        mod1 = src1.modality
        mod2 = src2.modality
        if mod1 == modA and mod2 == modB:
            return graph_generator(src1, src2)
        elif mod1 == modB and mod2 == modA:
            return graph_generator(src2, src1)
        else:
            msg = 'Crossmodal graph modality mismatch [%s/%s] vs. [%s/%s].' \
                  % (modA, modB, mod1, mod2)
            raise IOError(msg)
        
    return xgraph

def dump_graph_parser(graph_pkl):
    """
    
    Parameters
    ----------
    graph_pkl : str
        Path to 'graph.pkl' dumped file
        
    Returns
    -------
    dump : func
        func(g, uri) that pickle-dump g for given uri
    
    """
    def dump(g, uri):
        path = clicommon.replaceURI(graph_pkl, uri)
        with open(path, 'w') as f:
            pickle.dump(g, f)
    
    return dump

def out_parser(path):
    try:
       with open(path) as f: pass
    except IOError as e:
       return open(path, 'w')
    raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)
argparser.add_argument('output', type=out_parser, metavar='output.mdtm',
                       help='path to where to store output in MDTM format')

# == ILP ==

ogroup = argparser.add_argument_group('Optimization')
ogroup.add_argument('--method', metavar='N', default=-1,
                    choices=(-1, 0, 1, 2, 3, 4), 
                    help='set root relaxation solving method.')
ogroup.add_argument('--alpha', type=float, metavar='ALPHA', default=0.5,
                       help='set α value to ALPHA in objective function.')
ogroup.add_argument('--prune-mm', type=float, metavar='P', default=0.0,
                    help='set probability of mono-modal edges to zero '
                         'in case it is already lower than P.')
ogroup.add_argument('--stop-after', type=int, metavar='N', default=SUPPRESS,
                       help='stop optimization after N minutes')

# == Speaker ==
sgroup = argparser.add_argument_group('[speaker] modality')

# Speaker diarization     
msg = "path to source for speaker diarization. " + clicommon.msgURI()
sgroup.add_argument('--ss', type=mm_parser, metavar='source.mdtm', 
                    default=SUPPRESS, help=msg)
                    
sgroup.add_argument('--ss-param', metavar='param.pkl', 
                    type=ss_param_parser, dest='ssgraph', 
                    help='path to trained parameters for speaker diarization')

msg = "path to PLP feature files." + clicommon.msgURI()
sgroup.add_argument('--ss-plp', type=ss_plp_parser, metavar='uri.plp', help=msg)

# Speaker identification
sgroup.add_argument('--si', type=si_parser, metavar='source.etf0',
                    default=SUPPRESS,
                    help='path to source for speaker identification')
                    
sgroup.add_argument('--si-param', type=si_param_parser, metavar='param.pkl',
                          help='path to trained parameters for speaker '
                               'identification')

# == Head ==
hgroup = argparser.add_argument_group('[head] modality')

# Face clustering
msg = "path to source for head clustering. " + clicommon.msgURI()
hgroup.add_argument('--hh', type=mm_parser, metavar='source.mdtm', 
                    default=SUPPRESS, help=msg)

hgroup.add_argument('--hh-param', type=hh_param_parser, metavar='param.pkl',
                    dest='hhgraph', default=hh_param_parser(None),
                    help='path to trained parameters for head clustering')

msg = "path to precomputed similarity matrices." + clicommon.msgURI()
hgroup.add_argument('--hh-precomputed', type=hh_precomputed_parser, 
                    metavar='matrix.pkl', help=msg)

# Head recognition
hgroup.add_argument('--hi', type=hi_parser, metavar='source.nbl',
                    default=SUPPRESS,
                    help='path to source for head recognition')

hgroup.add_argument('--hi-param', type=hi_param_parser, metavar='param.pkl',
                    help='path to trained parameters for head '
                         'recognition')

# == Written ==
wgroup = argparser.add_argument_group('[written] modality')

# Written name detection
wgroup.add_argument('--wi', type=wi_parser, metavar='source.mdtm',
                    default=SUPPRESS, 
                    help='path to source for written name detection')

wgroup.add_argument('--wi-param', metavar='param.pkl', dest='wigraph',
                    type=wi_param_parser, default=wi_param_parser(None),
                    help='path to trained parameters for written name '
                         'detection')

# == Spoken ==
ngroup = argparser.add_argument_group('[spoken] modality')

# Spoken name detection
ngroup.add_argument('--ni', type=ni_parser, metavar='source.mdtm',
                    default=SUPPRESS,
                    help='path to source for spoken name detection')

ngroup.add_argument('--ni-param', type=ni_param_parser, metavar='param.pkl',
                    help='path to trained parameters for spoken name '
                         'detection')

# == Cross-modality ==
xgroup = argparser.add_argument_group('cross-modality')

xgroup.add_argument('--sh-param', metavar='param.pkl', type=x_param_parser,
                    dest='shgraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[speaker/head] cross-modal clustering.')

xgroup.add_argument('--sw-param', metavar='param.pkl', type=x_param_parser,
                    dest='swgraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[speaker/written] cross-modal clustering.')

xgroup.add_argument('--sn-param', metavar='param.pkl', type=x_param_parser,
                    dest='sngraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[speaker/spoken] cross-modal clustering.')

xgroup.add_argument('--hw-param', metavar='param.pkl', type=x_param_parser,
                    dest='hwgraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[head/written] cross-modal clustering.')

xgroup.add_argument('--hn-param', metavar='param.pkl', type=x_param_parser,
                    dest='hngraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[head/spoken] cross-modal clustering.')

xgroup.add_argument('--wn-param', metavar='param.pkl', type=x_param_parser,
                    dest='wngraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[written/spoken] cross-modal clustering.')

dgroup = argparser.add_argument_group('Debugging')

msg = "dump global graph before optimization." + clicommon.msgURI()
dgroup.add_argument('--dump-graph', type=dump_graph_parser, dest='dump',
                    metavar='graph.pkl', help=msg, default=SUPPRESS)

try:
    args = argparser.parse_args()
except IOError as e:
    sys.exit(e)


if hasattr(args, 'uris'):
    uris = args.uris

from pyannote.algorithm.clustering.optimization.graph import IdentityNode, LabelNode
from pyannote.algorithm.clustering.optimization.gurobi import GurobiModel
from pyannote.parser import MDTMParser

for u, uri in enumerate(uris):
    
    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()
    
    if hasattr(args, 'uem'):
        uem = args.uem(uri)
    else:
        uem = None
    
    # start with an empty graph
    G = nx.Graph()
    
    # speaker diarization
    if hasattr(args, 'ss'):
        
        if args.verbose:
            sys.stdout.write('   - [speaker/speaker] similarity graph\n')
            sys.stdout.flush()
        
        # get source
        ss_src = args.ss(uri)
        if uem is not None:
            ss_src = ss_src(uem, mode='intersection')
        
        # get PLP features
        plp = args.ss_plp(uri)
        
        # build speaker similarity graph
        g = args.ssgraph(ss_src, plp)
        
        # add it the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # speaker identification
    if hasattr(args, 'si'):
        pass
    
    # face clustering
    if hasattr(args, 'hh'):
        
        if args.verbose:
            sys.stdout.write('   - [head/head] similarity graph\n')
            sys.stdout.flush()
        
        # get source
        hh_src = args.hh(uri)
        if uem is not None:
            hh_src = hh_src(uem, mode='intersection')
        
        # get precomputed matrix
        precomputed = args.hh_precomputed(uri)
        
        # build head similarity graph
        g = args.hhgraph(hh_src, precomputed)
        
        # add it the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # face recognition
    if hasattr(args, 'hi'):
        pass
    
    # written name detection
    if hasattr(args, 'wi'):
        
        if args.verbose:
            sys.stdout.write('   - [written] identity graph\n')
            sys.stdout.flush()
        
        # get source
        wi_src = args.wi(uri)
        if uem is not None:
            wi_src = wi_src(uem, mode='intersection')
        
        # build written identity graph
        g = args.wigraph(wi_src)
        
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # spoken name detection
    if hasattr(args, 'ni'):
        pass
    
    # speaker/head
    if hasattr(args, 'shgraph'):
        
        if args.verbose:
            sys.stdout.write('   - [speaker/head] crossmodal graph\n')
            sys.stdout.flush()
        
        # build speaker/head graph
        g = args.shgraph(ss_src, hh_src)
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # speaker/written
    if hasattr(args, 'swgraph'):
        
        if args.verbose:
            sys.stdout.write('   - [speaker/written] crossmodal graph\n')
            sys.stdout.flush()
        
        # build speaker/written graph
        g = args.swgraph(ss_src, wi_src)
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # speaker/spoken
    if hasattr(args, 'sngraph'):
        
        if args.verbose:
            sys.stdout.write('   - [speaker/spoken] crossmodal graph\n')
            sys.stdout.flush()
        
        # build speaker/spoken graph
        g = args.sngraph(ss_src, ni_src)
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # head/written
    if hasattr(args, 'hwgraph'):
        
        if args.verbose:
            sys.stdout.write('   - [head/written] crossmodal graph\n')
            sys.stdout.flush()
        
        # build head/written graph
        g = args.hwgraph(hh_src, wi_src)
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # head/spoken
    if hasattr(args, 'hngraph'):
        
        if args.verbose:
            sys.stdout.write('   - [head/spoken] crossmodal graph\n')
            sys.stdout.flush()
        
        # build head/spoken graph
        g = args.sngraph(hh_src, ni_src)
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # written/spoken
    if hasattr(args, 'wngraph'):
        
        if args.verbose:
            sys.stdout.write('   - [written/spoken] crossmodal graph\n')
            sys.stdout.flush()
        
        # build written/spoken graph
        g = args.wngraph(wi_src, ni_src)
        # add it to the multimodal graph
        G.add_nodes_from(g.nodes_iter(data=True))
        G.add_edges_from(g.edges_iter(data=True))
    
    # add p=0 edge between all identity nodes
    inodes = [node for node in G if isinstance(node, IdentityNode)]
    for n, node in enumerate(inodes):
        for other_node in inodes[n+1:]:
            G.add_edge(node, other_node, probability=0.)
    
    # pruning
    for e,f,data in G.edges(data=True):
        
        # label/label pruning
        if isinstance(e, LabelNode) and isinstance(f, LabelNode):
            # mono-modal label/label pruning
            if e.modality == f.modality:
                if data['probability'] < args.prune_mm:
                    # keep track of pruning info
                    # only for debugging purpose
                    if hasattr(args, 'dump'):
                        G[e][f]['pruned'] = True
                    G[e][f]['probability'] = 0.
            # cross-modal label/label pruning
            else:
                pass
    
    # dump global graph
    if hasattr(args, 'dump'):
        args.dump(G, uri)
    
    # actual optimization
    if hasattr(args, 'stop_after'):
        stopAfter = args.stop_after * 60
    else:
        stopAfter = None
    
    model = GurobiModel(G, method=args.method, 
                           timeLimit=stopAfter, 
                           quiet=len(args.verbose) < 2)
    model.setObjective(alpha=args.alpha)
    model.optimize()
    
    # here write to file MIP GAP after end of optimization...
    status_num, status_msg = model.get_status()
    args.output.write('# %s: %s\n' % (uri, status_msg))
    
    if hasattr(args, 'ss'):
        ss_output = model.reconstruct(ss_src)
        MDTMParser().write(ss_output, f=args.output)
    
    if hasattr(args, 'hh'):
        hh_output = model.reconstruct(hh_src)
        MDTMParser().write(hh_output, f=args.output)
    
    
args.output.close()
    
