#!/usr/bin/env python
# encoding: utf-8

import networkx as nx
# from helper import ULabel

import pyannote.algorithms.community
from pyannote.base.association import Mapping, MElement
from pyannote.base.comatrix import Confusion, AutoConfusion

def __partition_to_cluster(partition):
    clusters = {}
    for node in partition:
        if partition[node] not in clusters:
            clusters[partition[node]] = []
        clusters[partition[node]].append(node)
    return clusters

def __autoconfusion_graph(A, neighborhood=0., normalize=False):
    
    # AutoConfusion matrix
    M = AutoConfusion(A, neighborhood=neighborhood, normalize=normalize)
    
    # Shape and labels
    Na, Na = M.shape
    alabels, alabels = M.labels
    
    G = nx.Graph()
    for i in range(Na):
        alabel_i = alabels[i]
        anode_i = MElement(A.modality, alabel_i)
        G.add_node(anode_i)
        for j in range(i+1, Na):
            alabel_j = alabels[j]
            anode_j = MElement(A.modality, alabel_j)
            if M[alabel_i, alabel_j] > 0.:
                G.add_edge(anode_i, anode_j)
                G[anode_i][anode_j]['weight'] = M[alabel_i, alabel_j]
    
    return G
    

def __confusion_graph(A, B, overlap=False, normalize=False):
    
    # Confusion matrix
    M = Confusion(A, B, normalize=normalize)
    
    # Shape and labels
    Na, Nb = M.shape
    alabels, blabels = M.labels
    
    # Confusion graph
    G = nx.Graph()
    for a, alabel in enumerate(alabels):
        anode = MElement(A.modality, alabel)
        G.add_node(anode)
        for blabel in blabels:
            bnode = MElement(B.modality, blabel)
            if a < 1:
                G.add_node(bnode)
            if M[alabel, blabel] > 0.:
                G.add_edge(anode, bnode)
                G[anode][bnode]['weight'] = M[alabel, blabel]
    
    if overlap:
        Ga = __autoconfusion_graph(A, neighborhood=0., normalize=normalize)
        G.add_edges_from(Ga.edges(data=True))
        
        Gb = __autoconfusion_graph(B, neighborhood=0., normalize=normalize)
        G.add_edges_from(Gb.edges(data=True))
        
    return G

def louvain(A, B, overlap=False, normalize=False):
    """
    Many-to-many mapping
    
    overlap: if True, also add intra-modality edges
    normalize: if True, normalize confusion matrix by total duration
    
    """
    G = __confusion_graph(A, B, overlap=overlap, normalize=normalize)
    
    if nx.number_connected_components(G) == len(G.nodes()):
        partition = {node: n for n, node in enumerate(G.nodes_iter())}
    else:
        # Community detection
        partition = pyannote.algorithms.community.best_partition(G)

    clusters = __partition_to_cluster(partition)
    
    # Many-to-many mapping
    mapping = Mapping(A.modality, B.modality)
    for cluster in clusters:
        nodes = clusters[cluster]
        key = [node.element for node in nodes if node.modality == A.modality]
        value = [node.element for node in nodes if node.modality == B.modality]
        mapping += (key, value)
    
    return mapping
            
    
    
    
