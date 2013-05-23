import pickle
f = open('/Volumes/Macintosh HD/Users/bredin/Desktop/SampleILPGraphs/LCP_EntreLesLignes_2011-07-08_192800.graph.pkl', 'r')
G = pickle.load(f)
f.close()

from pyannote.algorithm.clustering.optimization.graph import LabelNode, IdentityNode

g = {}

nodes = G.nodes()

name = {}
group = {}
for node in nodes:
    if isinstance(node, LabelNode):
        name[node] = node.label
        group[node] = node.modality
    elif isinstance(node, IdentityNode):
        name[node] = '[%s]' % node.identifier
        group[node] = 'ID'

g['nodes'] = [{'name': name[node], 'group': group[node]} for node in nodes]
g['inodes'] = [{'name': name[node], 'group': group[node]} 
               for node in nodes if isinstance(node, IdentityNode)]
g['lnodes'] = [{'name': name[node], 'group': group[node]} 
               for node in nodes if isinstance(node, LabelNode)]

I = {node: n for n, node in enumerate(nodes)}

g['links'] = [{'source': I[s], 'target': I[t], 'value': d[PROBABILITY]} 
              for s, t, d in G.edges_iter(data=True) if d[PROBABILITY] > 0.5]




import json
f = open('/Volumes/Macintosh HD/Users/bredin/Development/pyannote/www/d3/force/graph.json', 'w')
json.dump(g, f)
f.close()
