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

import networkx as nx
import numpy as np
from pyannote.algorithm.mpg.node import IdentityNode, LabelNode, TrackNode
from pyannote.algorithm.mpg.graph import RANK, PROBABILITY, SUBTRACK, COOCCURRING

def remove_nbest_identity(G, nbest):
    """Remove any identity nodes not in any n-best list"""
    inodes = [node for node in G if isinstance(node, IdentityNode)]
    remove = []
    for n, inode in enumerate(inodes):
        ranks = set([G[inode][node].get(RANK, np.inf) 
                     for node in G.neighbors_iter(inode)])
        if all([r>nbest for r in ranks]):
            remove.append(inode)
    G.remove_nodes_from(remove)
    return G


def add_unique_identity_constraint(G):
    """Add p=0. edges between all pairs of identity nodes"""
    inodes = [node for node in G if isinstance(node, IdentityNode)]
    for n, node in enumerate(inodes):
        for other_node in inodes[n+1:]:
            G.add_edge(node, other_node, {PROBABILITY: 0.})
    return G

def add_twin_tracks_constraint(G):
    """Add p=0 edges between all intra-modality 
       overlapping tracks (not subtracks)
    """ 
    
    # obtain the list of all modalities in graph
    modalities = set([n.modality for n in G if isinstance(n, TrackNode)])
    
    for modality in modalities:
        # obtain the list of tracks for this modality
        # (note that subtracks are not part of this list, 
        # they are hard-linked to their main track anyway)
        tnodes = [n for n in G if isinstance(n, TrackNode) \
                               and n.modality == modality \
                               and not G.node[n].get(SUBTRACK, False)]
        # loop on each pair of tracks and check for overlapping ones
        for n, node in enumerate(tnodes):
            for other_node in tnodes[n+1:]:
                # are they overlapping?
                if node.segment & other_node.segment:
                    G.add_edge(node, other_node, 
                               {PROBABILITY: 0., COOCCURRING: True})
    
    return G

def add_cooccurring_labels_contraint(G):
    
    # obtain the list of all modalities in graph
    modalities = set([n.modality for n in G if isinstance(n, LabelNode)])
    
    for modality in modalities:
        # obtain the list of labels for this modality
        lnodes = [n for n in G if isinstance(n, LabelNode) \
                               and n.modality == modality]
        # loop on each pair of labels and check if they are cooccurring
        for n, node in enumerate(lnodes):
            for other_node in lnodes[n+1:]:
                if G[node][other_node][COOCCURRING]:
                    G[node][other_node][PROBABILITY] = 0.
    
    return G


def meta_mpg(g):
    """Meta Multimodal Probability Graph
    
    Parameters
    ----------
    g : nx.Graph
        Multimodal probability graph
    
    Returns
    -------
    G : nx.Graph
        Multimodal probability graph where hard-linked nodes (p=1) are
        grouped into meta-nodes
    groups : list of lists
        Groups of nodes
    """
    
    # Group of hard-linked nodes
    # (ie. nodes connected with probability p=1)
    hard = nx.Graph()
    hard.add_nodes_from(g)
    hard.add_edges_from([(e,f) for e,f,d in g.edges_iter(data=True)
                               if d[PROBABILITY] == 1.])
    groups = nx.connected_components(hard)
    
    # meta graph with one node per group
    G = nx.blockmodel(g, groups, multigraph=True)
    
    meta = nx.Graph()
    for n in range(len(groups)):
        meta.add_node(n)
        for m in range(n+1, len(groups)):
            
            # do not do anything in case there is no edge
            # between those two meta-nodes
            if not G.has_edge(n, m):
                continue
            
            # obtain probabilities of all edges between n & m
            probabilities = [data[PROBABILITY] for data in G[n][m].values()]
            
            # raise an error in case of conflict (p=0 vs. p>0)
            if len(set(probabilities)) > 1 and 0 in probabilities:
                raise ValueError('conflict in meta-edges between %r and %r:' \
                                 'probabilities = %r' % (groups[n], 
                                                         groups[m], 
                                                         probabilities))
            
            meta.add_edge(n, m, {PROBABILITY: np.mean(probabilities)})
    
    return meta, groups


def log_mpg(g):
    """Make log-probability graph from probability graph
    
    Parameters
    ----------
    g: nx.Graph
        Probability graph
    
    Returns
    -------
    log : nx.Graph
        Input graph where each edge probability P is replaced by -log P
        except when P = 0 (otherwise -log P = +oo and subsequent shortest
        path algorithm fails quietly)
    
    """
    
    # new graph containing nodes from input graph
    log = nx.Graph()
    log.add_nodes_from(g.nodes_iter(data=True))
    
    # convert P to -log P for all input edges
    # do not add edge when P = 0
    for e,f,d in g.edges_iter(data=True):
        D = dict(d)
        p = d[PROBABILITY]
        if p > 0:
            D[PROBABILITY] = -np.log(p)
            log.add_edge(e,f,D)
    return log


def complete_mpg(g, existing=False):
    """Make complete graph from existing probability graph
    
    The returned complete probability graph only contains track nodes 
    and identity nodes (label nodes are usually not needed)
    
    Parameters
    ----------
    g : nx.Graph
        Probability graph
    existing : bool
        When True, even existings edge are updated in case a higher probability
        path connects the same nodes. By default, existing edges are kept
        unchanged.
    
    Returns
    -------
    complete : nx.Graph
        Complete probability graph. Each pair of nodes is weighted by the
        probability of the highest probability path between them.
    
    """
    
    # create new probability graph where each edge probability P 
    # is replaced by -log P except when P = 0 
    # (otherwise -log P = +oo and shortest path algorithm quietly fails)
    log = log_mpg(g)
    
    # compute maximum probability path between each pair of nodes
    # where the probability of a path is the product of every encountered
    # probabilities (actually -log π pij)
    shortest = nx.shortest_path_length(log, weight=PROBABILITY)
    
    # create new complete probability graph where each edge probability P
    # is replaced by the probability of the maximum probability path
    # except when P = 0 or when 'existing' is True and the edge exists 
    # in the original probability graph (in these case P is kept unchanged)
    complete = nx.Graph()
    complete.add_nodes_from(g.nodes_iter(data=True))
    nodes = complete.nodes()
    
    for n, e in enumerate(nodes):
        for f in nodes[n+1:]:
            
            # special behavior in case there is an edge connecting the 2 nodes
            # in the original graph: don't update if p=0 or if existing=False
            if g.has_edge(e,f):
                D = dict(g[e][f])
                if D[PROBABILITY] != 0. and existing:
                    D[PROBABILITY] = np.exp(-shortest[e][f])
                # else:
                #     pass
            else:
                # in case e and f are in two different connected components
                # no shortest path can be computed -- therefore we need
                # to test whether it happens and set probability to 0
                if e in shortest and f in shortest[e]:
                    D = {PROBABILITY: np.exp(-shortest[e][f])}
                else:
                    D = {PROBABILITY: 0.}
            
            # add edge with updated probability
            # all other edge variables are kept unchanged
            complete.add_edge(e, f, D)
    
    return complete


def _add_shortest_edge(complete, g, existing, e, f, shortest):
    # special behavior in case there is an edge connecting the 2 nodes
    # in the original graph: don't update if p=0 or if existing=False
    if g.has_edge(e,f):
        D = dict(g[e][f])
        if D[PROBABILITY] != 0. and existing:
            D[PROBABILITY] = np.exp(-shortest[e][f])
        # else:
        #     pass
    else:
        # in case e and f are in two different connected components
        # no shortest path can be computed -- therefore we need
        # to test whether it happens and set probability to 0
        if e in shortest and f in shortest[e]:
            D = {PROBABILITY: np.exp(-shortest[e][f])}
        else:
            D = {PROBABILITY: 0.}
            
    # add edge with updated probability
    # all other edge variables are kept unchanged
    complete.add_edge(e, f, D)



def complete_mpg2(g, existing=False):
    """Make complete graph from existing probability graph
    
    The returned complete probability graph only contains track nodes 
    and identity nodes (label nodes are usually not needed)
    
    Parameters
    ----------
    g : nx.Graph
        Probability graph
    existing : bool
        When True, even existings edge are updated in case a higher probability
        path connects the same nodes. By default, existing edges are kept
        unchanged.
    
    Returns
    -------
    complete : nx.Graph
        Complete probability graph. Each pair of nodes is weighted by the
        probability of the highest probability path between them.
    
    """
    
    # create new probability graph where each edge probability P 
    # is replaced by -log P except when P = 0 
    # (otherwise -log P = +oo and shortest path algorithm quietly fails)
    log = log_mpg(g)
    
    inodes = [node for node in log if isinstance(node, IdentityNode)]
    tnodes = [node for node in log if isinstance(node, TrackNode)]
    
    complete = nx.Graph()
    complete.add_nodes_from(inodes)
    complete.add_nodes_from(tnodes)
    
    # track to identity shortest paths
    for inode in inodes:
        # create new graph where all other identity nodes are removed
        # in order to prevent meaningless shortest paths
        _log = nx.Graph(log)
        _log.remove_nodes_from([n for n in inodes if n != inode])
        shortest = nx.shortest_path_length(_log, source=inode, weight=PROBABILITY)
        for tnode in shortest:
            if isinstance(tnode, TrackNode):
                _add_shortest_edge(complete, g, existing, 
                                   inode, tnode, {inode: shortest})
    
    # track to track shortest paths
    _log = nx.Graph(log)
    _log.remove_nodes_from(inodes)
    shortest = nx.shortest_path_length(_log, weight=PROBABILITY)
    for tnode1 in shortest:
        if isinstance(tnode1, TrackNode):
            for tnode2 in shortest[tnode1]:
                if isinstance(tnode2, TrackNode):
                    _add_shortest_edge(complete, g, existing, 
                                       tnode1, tnode2, shortest)
    
    return complete
