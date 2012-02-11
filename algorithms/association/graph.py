#!/usr/bin/env python
# encoding: utf-8

import networkx as nx
from helper import ULabel
import pyannote.algorithms.community

def partition_to_cluster(partition):
    clusters = {}
    for node in partition:
        if partition[node] not in clusters:
            clusters[partition[node]] = []
        clusters[partition[node]].append(node)
    return clusters

def louvain(A, B):
    """
    Many-to-many mapping
    """
    
    # Confusion matrix
    M = A * B
    
    # Shape and labels
    Na, Nb = M.shape
    alabels, blabels = M.labels
    
    # Confusion graph
    G = nx.Graph()
    for alabel in alabels:
        anode = ULabel('A', alabel)
        for blabel in blabels:
            bnode = ULabel('B', blabel)
            G.add_edge(anode, bnode)
            G[anode][bnode]['weight'] = M[alabel, blabel]
    
    # Community detection
    partition = pyannote.algorithms.community.best_partition(G)
    clusters = partition_to_cluster(partition)
    
    # Many-to-many mapping
    mapping = {}
    for cluster in clusters:
        nodes = clusters[cluster]
        key = tuple([node.label for node in nodes if node.u == 'A'])
        value = tuple([node.label for node in nodes if node.u == 'B'])
        mapping[key] = value
    
    return mapping
    
            
    
    
    
