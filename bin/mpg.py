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
import numpy as np
from pyannote.algorithm.mpg.graph import MultimodalProbabilityGraph
from pyannote.algorithm.mpg.graph import SegmentationGraph, CrossModalGraph
from pyannote import Annotation, Scores

# New argument parser
from argparse import ArgumentParser, SUPPRESS
from pyannote import clicommon
argparser = ArgumentParser(parents=[clicommon.parser],
                           description='Multimodal Probability Graph')

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
            .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)


from pyannote.algorithm.mpg.graph import LabelSimilarityGraph


def ss_param_parser(param_pkl):
    """Speaker diarization

    - [L] label nodes
    - [T] track nodes
    - [L] -- [L] soft edges
    - [T] == [L] hard edges

    Parameters
    ----------
    param_pkl : str
        Path to 'param.pkl' parameter file.

    Returns
    -------
    graph_generator : LabelSimilarityGraph
        callable (e.g. graph_generator(annotation, feature)) object
        that returns a label similarity graph [L] -- [L] augmented
        with a diarization graph [T] == [L]
    """

    with open(param_pkl, 'r') as f:
        params = pickle.load(f)

    mmx = params.pop('__mmx__')
    s2p = params.pop('__s2p__')

    class SSGraph(LabelSimilarityGraph, mmx):
        def __init__(self):
            super(SSGraph, self).__init__(s2p=s2p, **params)

    ssGraph = SSGraph()
    return ssGraph


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


def si_parser(path):
    """Speaker identification scores

    Parameters
    ----------
    path : str
        Path to speaker identification scores

    Returns
    -------
    load_scores : func or ScoresParser
        callable that takes uri as unique argument and return speaker
        identification scores as Panda MultiIndex (segment/track) DataFrame
    """
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
            .read(clicommon.replaceURI(path, u), uri=u)(u)
    else:
        return AnnotationParser().read(path)


from pyannote.algorithm.mpg.graph import ScoresGraph, AnnotationGraph


def id_param_parser(param_pkl):
    """Speaker identification graph

    - [T] track nodes
    - [I] identity nodes
    - [T] -- [I] soft edges in case of scores
    - [T] == [I] hard edges in case of annotation

    Parameters
    ----------
    param_pkl : str
        Path to 'param.pkl' parameter file.
        If "identity", scores are considered as probabilities

    Returns
    -------
    graph_generator : ScoresGraph
    """

    if param_pkl == 'identity':
        params = {}
        s2p = lambda p: p
    else:
        with open(param_pkl, 'r') as f:
            params = pickle.load(f)
        s2p = params.pop('__s2p__')

    class SIGraph(ScoresGraph):
        def __init__(self):
            super(SIGraph, self).__init__(s2p=s2p, **params)

    scoresGraph = SIGraph()
    annotationGraph = AnnotationGraph()

    def getGraph(annotationOrScores):
        if isinstance(annotationOrScores, Scores):
            scores = annotationOrScores
            return scoresGraph(scores)
        elif isinstance(annotationOrScores, Annotation):
            annotation = annotationOrScores
            return annotationGraph(annotation)

    return getGraph


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
        hhGraph = HHGraph()
    else:
        with open(param_pkl, 'r') as f:
            params = pickle.load(f)

        mmx = params.pop('__mmx__')
        s2p = params.pop('__s2p__')

        class HHGraph(LabelSimilarityGraph, mmx):
            def __init__(self):
                super(HHGraph, self).__init__(s2p=s2p, **params)

        hhGraph = HHGraph()

    return hhGraph

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
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
            .read(clicommon.replaceURI(path, u), uri=u, modality='head')(u)
    else:
        return AnnotationParser().read(path)


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


from pyannote.algorithm.mpg.graph import AnnotationGraph


def wi_param_parser(path):
    """Written names

    - [T] track nodes
    - [I] identity nodes
    - [T] == [I] hard edges

    """
    if path is None:
        graph_generator = AnnotationGraph()
    else:
        raise NotImplementedError('--wi-param option is not supported yet.')
    return graph_generator


def ni_parser(path):
    if clicommon.containsURI(path):
        return lambda u: AnnotationParser()\
            .read(clicommon.replaceURI(path, u), uri=u, modality='spoken')(u)
    else:
        return AnnotationParser().read(path)


def ni_param_parser(path):
    if path is None:
        graph_generator = AnnotationGraph()
    else:
        raise NotImplementedError('--ni-param option is not supported yet.')
    return graph_generator

from pyannote.algorithm.mpg.graph import TrackCooccurrenceGraph


def x_param_parser(param_pkl):
    """Cross-modal graph

    - [t1] sub-track nodes (first modality)
    - [t2] sub-track nodes (second modality)
    - [t1] -- [t2] soft edges

    - [T1] track nodes (first modality)
    - [T2] track nodes (second modality)
    - [t1] == [T1] hard edges
    - [t2] == [T2] hard edges

    Parameters
    ----------
    param_pkl : str
        Path to 'param.pkl' parameter file

    Returns
    -------
    graph_generator : TrackCooccurrenceGraph
        callable (e.g. graph_generator(speaker, head)) object
        that returns a label cooccurrence graph

    """
    with open(param_pkl, 'r') as f:
        params = pickle.load(f)

    tcg = TrackCooccurrenceGraph(**params)

    def xgraph(src1, src2, only1x1):
        modA = tcg.modalityA
        modB = tcg.modalityB
        mod1 = src1.modality
        mod2 = src2.modality
        if mod1 == modA and mod2 == modB:
            return tcg(src1, src2, only1x1=only1x1)
        elif mod1 == modB and mod2 == modA:
            return tcg(src2, src1, only1x1=only1x1)
        else:
            msg = 'Crossmodal graph modality mismatch [%s/%s] vs. [%s/%s].' \
                  % (modA, modB, mod1, mod2)
            raise IOError(msg)

    return xgraph


def sn_param_parser(prob_txt):
    return CrossModalGraph(fileName=prob_txt, modalityA='spoken', modalityB='speaker')


msg = "path where to store multimodal probability graph." + clicommon.msgURI()
argparser.add_argument('output', type=str, metavar='graph.pkl', help=msg)

msg = "remove identity nodes not in any n-best lists."
argparser.add_argument('--nbest', metavar='N', type=int, default=SUPPRESS,
                       help=msg)

# == Speaker ==
sgroup = argparser.add_argument_group('[speaker] modality')

# Speaker diarization

msg = "path to source for speaker diarization. " + clicommon.msgURI()
sgroup.add_argument('--ss', type=mm_parser, metavar='source.mdtm',
                    default=SUPPRESS, help=msg)

msg = "path to trained parameters for speaker diarization."
sgroup.add_argument('--ss-param', metavar='param.pkl',
                    type=ss_param_parser, dest='ssgraph', default=SUPPRESS,
                    help=msg)

msg = "path to PLP feature files." + clicommon.msgURI()
sgroup.add_argument('--ss-plp', type=ss_plp_parser, metavar='uri.plp', help=msg)

msg = "do not trust input speaker diarization (ie. no hard edges between speech turns)"
sgroup.add_argument('--ss-dont-trust', action='store_true', help=msg)

# Speaker identification

msg = "path to speaker identification scores (or annotation)."
sgroup.add_argument('--si', type=si_parser, metavar='source.etf0',
                    default=SUPPRESS, help=msg)

msg = "path to trained parameters for speaker identification. use 'identity' when scores are probabilities."
sgroup.add_argument('--si-param', metavar='param.pkl',
                    nargs='?', const=id_param_parser('identity'),
                    type=id_param_parser, dest='sigraph', default=SUPPRESS,
                    help=msg)

# == Head ==
hgroup = argparser.add_argument_group('[head] modality')

# Face clustering
msg = "path to source for head clustering. " + clicommon.msgURI()
hgroup.add_argument('--hh', type=mm_parser, metavar='source.mdtm',
                    default=SUPPRESS, help=msg)

# msg = 'get rid of face tracks in FILE'
# hgroup.add_argument('--hh-remove', type=, metavar='FILE',
#                     default=SUPPRESS, help=msg)

msg = 'path to trained parameters for head clustering'
hgroup.add_argument('--hh-param', type=hh_param_parser, metavar='param.pkl',
                    dest='hhgraph', default=SUPPRESS, help=msg)

msg = "path to precomputed similarity matrices." + clicommon.msgURI()
hgroup.add_argument('--hh-precomputed', type=hh_precomputed_parser,
                    metavar='matrix.pkl', help=msg)

# Head recognition
msg = "path to source for head recognition."
hgroup.add_argument('--hi', type=hi_parser, metavar='source.etf0',
                    default=SUPPRESS, help=msg)

msg = 'path to trained parameters for face recognition. use "identity" when scores are probabilities.'
hgroup.add_argument('--hi-param', metavar='param.pkl',
                    nargs='?', const=id_param_parser('identity'),
                    type=id_param_parser, dest='higraph', default=SUPPRESS,
                    help=msg)

# == Written ==
wgroup = argparser.add_argument_group('[written] modality')

# Written name detection
msg = 'path to source for written name detection'
wgroup.add_argument('--wi', type=wi_parser, metavar='source.mdtm',
                    default=SUPPRESS, help=msg)

msg = 'path to trained parameters for written name detection'
wgroup.add_argument('--wi-param', type=wi_param_parser, metavar='param.pkl',
                    default=wi_param_parser(None), dest='wigraph', help=msg)

# == Spoken ==
ngroup = argparser.add_argument_group('[spoken] modality')

# Spoken name detection
msg = 'path to source for spoken name detection'
ngroup.add_argument('--ni', type=ni_parser, metavar='source.mdtm',
                    default=SUPPRESS, help=msg)

msg = 'path to trained parameters for spoken name detection'
ngroup.add_argument('--ni-param', type=ni_param_parser, metavar='param.pkl',
                    default=ni_param_parser(None), dest='nigraph', help=msg)

# == Cross-modality ==
xgroup = argparser.add_argument_group('cross-modality')

xgroup.add_argument('--only1x1', action='store_true',
                    help='only add edges when there is exactly one track'
                         'in each modality')
xgroup.add_argument('--sh-param', metavar='param.pkl', type=x_param_parser,
                    dest='shgraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[speaker/head] cross-modal clustering.')

xgroup.add_argument('--sw-param', metavar='param.pkl', type=x_param_parser,
                    dest='swgraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[speaker/written] cross-modal clustering.')

xgroup.add_argument('--sn-param', metavar='prob.txt', type=sn_param_parser,
                    dest='sngraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[speaker/spoken] cross-modal clustering.')

msg = 'Temporal difference up to which speaker and spoken nodes should be connected.'
xgroup.add_argument('--sn-tmax', metavar='SECONDS', type=float,
                    default=500, help=msg)

xgroup.add_argument('--hw-param', metavar='param.pkl', type=x_param_parser,
                    dest='hwgraph', default=SUPPRESS,
                    help='path to trained parameters for '
                         '[head/written] cross-modal clustering.')

# xgroup.add_argument('--hn-param', metavar='param.pkl', type=nh_param_parser,
#                     dest='hngraph', default=SUPPRESS,
#                     help='path to trained parameters for '
#                          '[head/spoken] cross-modal clustering.')

# xgroup.add_argument('--wn-param', metavar='param.pkl', type=nw_param_parser,
#                     dest='wngraph', default=SUPPRESS,
#                     help='path to trained parameters for '
#                          '[written/spoken] cross-modal clustering.')

try:
    args = argparser.parse_args()
except IOError as e:
    sys.exit(e)

if hasattr(args, 'uris'):
    uris = args.uris

from pyannote.algorithm.mpg.util import *


for u, uri in enumerate(uris):

    if args.verbose:
        sys.stdout.write('[%d/%d] %s\n' % (u+1, len(uris), uri))
        sys.stdout.flush()

    # make sure output file will not be overwritten
    path = clicommon.replaceURI(args.output, uri)
    file_exists = False
    try:
        with open(path, 'r') as foutput:
            file_exists = True
    except IOError as e:
        foutput = open(path, 'w')
    if file_exists:
        raise IOError('ERROR: output file %s already exists. Delete it first.\n' % path)

    if hasattr(args, 'uem'):
        uem = args.uem(uri)
    else:
        uem = None

    # start with an empty graph
    G = MultimodalProbabilityGraph()

    # SPEAKER DIARIZATION & IDENTIFICATION
    # ====================================

    # load speaker diarization input (ss)
    if hasattr(args, 'ss'):
        ss_src = args.ss(uri=uri, modality='speaker')
        if uem is not None:
            ss_src = ss_src.crop(uem, mode='loose')
    else:
        ss_src = None

    # load speaker identification scores (si)
    if hasattr(args, 'si'):
        si_src = args.si(uri=uri, modality='speaker')
        if uem is not None:
            si_src = si_src.crop(uem, mode='loose')
        if ss_src is None:
            if isinstance(si_src, Scores):
                ss_src = si_src.to_annotation(threshold=np.inf)
            elif isinstance(si_src, Annotation):
                ss_src = si_src.anonymize()
    else:
        si_src = None

    # add speech turns to graph
    if ss_src is not None:

        if args.verbose:
            sys.stdout.write('   - [speaker] speech turns\n')
            sys.stdout.flush()

        g = SegmentationGraph()(ss_src)
        G.add(g)

    # speaker diarization
    if hasattr(args, 'ssgraph'):

        if args.verbose:
            sys.stdout.write('   - [speaker/speaker] diarization graph\n')
            sys.stdout.flush()

        # get PLP features
        plp = args.ss_plp(uri)

        # build speaker similarity graph
        if args.ss_dont_trust:
            g = args.ssgraph(ss_src.anonymize_tracks(), plp)
        else:
            g = args.ssgraph(ss_src, plp)
        # add it the multimodal graph
        G.add(g)

    # speaker identification
    if hasattr(args, 'sigraph'):

        if args.verbose:
            sys.stdout.write('   - [speaker] recognition graph\n')
            sys.stdout.flush()

        # make sure the tracks are named the same way
        # in speaker diarization and speaker identification
        if ss_src is not None:
            assert ss_src.get_timeline() == si_src.get_timeline(), \
                "speaker diarization and identification timelines are not the same"
            for s in ss_src:
                assert ss_src.tracks(s) == si_src.tracks(s), \
                    "ss and si tracks are not the same " \
                    "%r: %r vs. %r" % (s, ss_src.tracks(s), si_src.tracks(s))

        # build speaker identity graph
        g = args.sigraph(si_src)

        # add it to the multimodal graph
        G.add(g)

    # HEAD CLUSTERING & RECOGNITION
    # =============================

    # load face clustering input (hh)
    if hasattr(args, 'hh'):
        hh_src = args.hh(uri)
        if uem is not None:
            hh_src = hh_src.crop(uem, mode='loose')
    else:
        hh_src = None

    # load head identification scores (hi)
    if hasattr(args, 'hi'):
        hi_src = args.hi(uri)
        if uem is not None:
            hi_src = hi_src.crop(uem, mode='loose')
        if hh_src is None:
            hh_src = hi_src.to_annotation(threshold=np.inf)
    else:
        hi_src = None

    # face tracks
    if hh_src is not None:

        if args.verbose:
            sys.stdout.write('   - [head] face tracks\n')
            sys.stdout.flush()

        g = SegmentationGraph()(hh_src)
        G.add(g)

    # face clustering
    if hasattr(args, 'hhgraph'):

        if args.verbose:
            sys.stdout.write('   - [head/head] diarization graph\n')
            sys.stdout.flush()

        # get precomputed matrix
        precomputed = args.hh_precomputed(uri)

        # build head similarity graph
        g = args.hhgraph(hh_src, precomputed)

        # add it the multimodal graph
        G.add(g)

    # face recognition
    if hasattr(args, 'higraph'):

        if args.verbose:
            sys.stdout.write('   - [head] recognition graph\n')
            sys.stdout.flush()

        # # make sure the tracks are named the same way
        # # in head clustering and head recognition
        # if hh_src is not None:
        #     assert hh_src.get_timeline() == hi_src.get_timeline() and \
        #            all([hh_src.tracks(s) == hi_src.track(s) for s in hh_src]), \
        #            "head clustering and recognition tracks are not the same"

        # build head identity graph
        g = args.higraph(hi_src)

        # add it to the multimodal graph
        G.add(g)

    # WRITTEN NAMES
    # =============

    if hasattr(args, 'wi'):
        wi_src = args.wi(uri=uri, modality='written')
        if uem is not None:
            wi_src = wi_src.crop(uem, mode='loose')
    else:
        wi_src = None

    # written name detection
    if hasattr(args, 'wi'):

        if args.verbose:
            sys.stdout.write('   - [written] identity graph\n')
            sys.stdout.flush()

        # build written identity graph
        g = args.wigraph(wi_src)

        # add it to the multimodal graph
        G.add(g)

    # SPOKEN NAMES
    # ============

    if hasattr(args, 'ni'):
        ni_src = args.ni(uri=uri, modality='spoken')
        if uem is not None:
            ni_src = ni_src.crop(uem, mode='loose')
    else:
        ni_src = None

    # spoken name detection
    if hasattr(args, 'ni'):

        if args.verbose:
            sys.stdout.write('   - [spoken] identity graph\n')
            sys.stdout.flush()

        # build written identity graph
        g = args.nigraph(ni_src)

        # add it to the multimodal graph
        G.add(g)

    # speaker/head
    if hasattr(args, 'shgraph'):

        if args.verbose:
            sys.stdout.write('   - [speaker/head] crossmodal graph\n')
            sys.stdout.flush()

        # build speaker/head graph
        g = args.shgraph(ss_src, hh_src, args.only1x1)

        # add it to the multimodal graph
        G.add(g)

    # speaker/written
    if hasattr(args, 'swgraph'):

        if args.verbose:
            sys.stdout.write('   - [speaker/written] crossmodal graph\n')
            sys.stdout.flush()

        # build speaker/written graph
        g = args.swgraph(ss_src, wi_src, args.only1x1)

        # add it to the multimodal graph
        G.add(g)

    # speaker/spoken
    if hasattr(args, 'sngraph'):

        if args.verbose:
            sys.stdout.write('   - [speaker/spoken] crossmodal graph\n')
            sys.stdout.flush()

        args.sngraph.get_prob.tmax = args.sn_tmax

        # build speaker/spoken graph
        g = args.sngraph(ni_src, ss_src)

        # add it to the multimodal graph
        G.add(g)

    # head/written
    if hasattr(args, 'hwgraph'):

        if args.verbose:
            sys.stdout.write('   - [head/written] crossmodal graph\n')
            sys.stdout.flush()

        # build head/written graph
        g = args.hwgraph(hh_src, wi_src, args.only1x1)

        # add it to the multimodal graph
        G.add(g)

    # head/spoken
    if hasattr(args, 'hngraph'):

        if args.verbose:
            sys.stdout.write('   - [head/spoken] crossmodal graph\n')
            sys.stdout.flush()

        # build head/spoken graph
        g = args.sngraph(hh_src, ni_src, args.only1x1)

        # add it to the multimodal graph
        G.add(g)

    # written/spoken
    if hasattr(args, 'wngraph'):

        if args.verbose:
            sys.stdout.write('   - [written/spoken] crossmodal graph\n')
            sys.stdout.flush()

        # build written/spoken graph
        g = args.wngraph(wi_src, ni_src, args.only1x1)

        # add it to the multimodal graph
        G.add(g)

    # if hasattr(args, 'nbest'):
    #     G = remove_nbest_identity(G, args.nbest)
    G.add_identity_constraints()
    G.add_track_constraints()

    # dump graph
    nx.write_gpickle(G, foutput)
    foutput.close()
