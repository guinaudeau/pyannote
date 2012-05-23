from pyannote.parser import XGTFParser, TRSParser
from pyannote.algorithm.tagging import DirectTagger

xpath = '/Users/bredin/Data/QCompere/dryrun/dev/manual/xgtf/BFMTV_BFMStory_2011-05-11_175900_dev0.xgtf'
ipath = '/Users/bredin/Data/QCompere/dryrun/dev/auto/idx/BFMTV_BFMStory_2011-05-11_175900.MPG.idx'
tpath = '/Users/bredin/Data/QCompere/dryrun/dev/manual/trs/BFMTV_BFMStory_2011-05-11_175900_dev0.trs'

xgtf = XGTFParser().read(xpath, ipath, video='sample')
trs = TRSParser().read(tpath, video='sample')
speaker = trs(modality="speaker")
written = xgtf(modality="written (alone)")
head = xgtf(modality="head")
common_timeline = (speaker.timeline + written.timeline + head.timeline).segmentation()
tagger = DirectTagger()
speaker = tagger(speaker, common_timeline)
head = tagger(head, common_timeline)
written = tagger(written, common_timeline)


# =========================

from pyannote import Annotation
def counts(annotation):
    tagger = DirectTagger()
    annotation = tagger(annotation, annotation.timeline.segmentation())
    count = Annotation(multitrack=False, modality=annotation.modality)
    for segment in annotation:
        count[segment] = len(annotation[segment, :])
    return count

# =========================

import networkx as nx

# build a complete graph with one node per track
# the edge between two nodes is weighted as follow:
# 0.0 if tracks are for the same segment
# N(0.3, std) if labels are different
# N(0.7, std) if labels are identical
def monograph(annotation, std):
    g = nx.Graph(name=annotation.modality)
    for segment, track, label in annotation.iterlabels():
        node = (annotation.modality, segment, track, label)
        g.add_edge(node, node, weight=1.)
        for other_node in g.nodes():
            if node == other_node:
                continue
            other_segment = other_node[1]
            if segment == other_segment:
                weight = 0.0
            else:
                other_label = other_node[3]
                if label == other_label:
                    weight = 0.7 + std * float(np.random.randn(1))
                else:
                    weight = 0.3 + std * float(np.random.randn(1))
            g.add_edge(node, other_node, weight=weight)
    return g

# build a graph with cross-modality edges
def crossgraph(annotation1, annotation2, std):
    g = nx.Graph(name='%s <--> %s' % (annotation1.modality,
                                      annotation2.modality))
    for segment in annotation1.timeline + annotation2.timeline:
        if segment in annotation1 and segment in annotation2:
            tracks1 = annotation1[segment, :]
            tracks2 = annotation2[segment, :]
            for track1, label1 in tracks1.iteritems():
                node1 = (annotation1.modality, segment, track1, label1)
                for track2, label2 in tracks2.iteritems():
                    node2 = (annotation2.modality, segment, track2, label2)
                    if label1 == label2:
                        weight = 0.7 + std * float(np.random.randn(1))
                    else:
                        weight = 0.3 + std * float(np.random.randn(1))
                    g.add_edge(node1, node2, weight=weight)
    return g


# =========================

import numpy as np
import networkx as nx


# for std in [0.01, 0.05, 0.1, 0.2, 0.3, 0.4]:
for std in [0.5, 0.6]:
    diarization = speaker.copy()
    gs = monograph(diarization, std)
    ms = np.array(nx.to_numpy_matrix(gs))
    labels = sklearn.cluster.spectral_clustering(ms, k=len(speaker.labels()))
    for n, node in enumerate(gs.nodes()):
        segment = node[1]
        track = node[2]
        diarization[segment, track] = labels[n]
    der = pyannote.metric.DiarizationErrorRate()
    print std, der(speaker, diarization)

# 0.01 0.00180536521826
# 0.05 0.00180536521826
# 0.1 0.00180536521826
# 0.2 0.0126046319342
# 0.3 0.126483118951
# 0.4 0.27012653611
# 0.5 0.290453082741
# 0.6 0.340487490218

# total number of labels
k = len(set(speaker.labels()) | set(head.labels()))

std_speaker = 0.4
std_head = 0.4
gspeaker = monograph(speaker, std_speaker)
ghead = monograph(head, std_head)
std_cross = 0.4
gcross = crossgraph(speaker, head, std_cross)
gcross.add_edges_from(gspeaker.edges_iter(data=True))
gcross.add_edges_from(ghead.edges_iter(data=True))

diarization = {}
diarization[speaker.modality] = speaker.copy()
diarization[head.modality] = head.copy()
diarization['cross-' + speaker.modality] = speaker.copy()
diarization['cross-' + head.modality] = head.copy()

mspeaker = np.array(nx.to_numpy_matrix(gspeaker))
labels = sklearn.cluster.spectral_clustering(mspeaker, k=k)
for n, node in enumerate(gspeaker.nodes()):
    modality = node[0]
    segment = node[1]
    track = node[2]
    label = labels[n]
    diarization[modality][segment, track] = label

mhead = np.array(nx.to_numpy_matrix(ghead))
labels = sklearn.cluster.spectral_clustering(mhead, k=k)
for n, node in enumerate(ghead.nodes()):
    modality = node[0]
    segment = node[1]
    track = node[2]
    label = labels[n]
    diarization[modality][segment, track] = label

mcross = np.array(nx.to_numpy_matrix(gcross))
labels = sklearn.cluster.spectral_clustering(mcross, k=k)
for n, node in enumerate(gcross.nodes()):
    modality = node[0]
    segment = node[1]
    track = node[2]
    label = labels[n]
    diarization['cross-' + modality][segment, track] = label

# der(speaker, diarization['speaker'])
# 0.6701098389897494
# der(speaker, diarization['cross-speaker'])
# 0.495175985515617
# der(head, diarization['head'])
# 0.5534796025963146
# der(head, diarization['cross-head'])
# 0.11128079421497743


from pyannote.algorithm.util.community import modularity
mspeaker = np.array(nx.to_numpy_matrix(gspeaker))
der = pyannote.metric.DiarizationErrorRate()
for k in range(2, 20):
    labels = sklearn.cluster.spectral_clustering(mspeaker, k=k)
    aspeaker = speaker.copy()
    for n, node in enumerate(gspeaker.nodes()):
        modality = node[0]
        segment = node[1]
        track = node[2]
        label = labels[n]
        aspeaker[segment, track] = label
    
    partition = {node: labels[n] for n, node in enumerate(gspeaker.nodes())}
    print k, modularity(partition, gspeaker), der(speaker, aspeaker)

# mono-modal spectral clustering
# k modularity der
# 2 3.40902054388e-05 0.695455191179
# 3 0.160042677299 0.276860712997
# 4 0.165128911815 0.276860712997
# 5 0.169212576602 0.0535847761591
# 6 0.163062712109 0.0724198386976
# 7 0.137183475234 0.208330366296
# 8 0.101894344404 0.38108348864
# 9 0.117004019351 0.247879388184
# 10 0.0957805434496 0.369069329963
# 11 0.0934017077537 0.396806079593
# 12 0.0841008048541 0.40443470794
# 13 0.0816058418057 0.50095754416

mcross = np.array(nx.to_numpy_matrix(gcross))
der = pyannote.metric.DiarizationErrorRate()
for k in range(4, 30, 2):
    labels = sklearn.cluster.spectral_clustering(mcross, k=k)
    aspeaker = speaker.copy()
    partition = {}
    for n, node in enumerate(gcross.nodes()):
        modality = node[0]
        if modality == 'speaker':
            segment = node[1]
            track = node[2]
            label = labels[n]
            aspeaker[segment, track] = label
            partition[node] = label
    print k, modularity(partition, gspeaker), der(speaker, aspeaker), len(aspeaker.labels())

# 4 0.129085956495 0.461775108292 2
# 6 0.165981094393 0.276729014623 3
# 8 0.170161858217 0.0654815293299 5
# 10 0.171312120009 0.120381094262 4
# 12 0.137720344779 0.21134735656 7
# 14 0.137513660644 0.18091295968 7
# 16 0.111289263563 0.313766961958 9
# 18 0.0990034219798 0.393081210565 11
# 20 0.0801979046402 0.458179742666 13


mcross = np.array(nx.to_numpy_matrix(gcross))
der = pyannote.metric.DiarizationErrorRate()
for k in range(4, 30, 2):
    labels = sklearn.cluster.spectral_clustering(mcross, k=k)
    ahead = head.copy()
    partition = {}
    for n, node in enumerate(gcross.nodes()):
        modality = node[0]
        if modality == 'head':
            segment = node[1]
            track = node[2]
            label = labels[n]
            ahead[segment, track] = label
            partition[node] = label
    print k, modularity(partition, ghead), der(head, ahead), len(ahead.labels())


# 4 6.50916360255e-06 0.6735608939 2
# 6 0.116993363986 0.489419046452 3
# 8 0.13855453633 0.38262409609 4
# 10 0.133644698306 0.144134902153 7
# 12 0.133846451973 0.143834211709 7
# 14 0.132440129295 0.111280794215 8
# 16 0.132440129295 0.111280794215 8
# 18 0.132440129295 0.111280794215 8
# 20 0.104414478433 0.254221922621 9
# 22 0.10439084002 0.257689667851 9
# 24 0.104196657056 0.243763124566 9

k = 8
mhead = np.array(nx.to_numpy_matrix(ghead))
labels = sklearn.cluster.spectral_clustering(mhead, k=k)
ahead = head.copy()
for n, node in enumerate(ghead.nodes()):
    modality = node[0]
    segment = node[1]
    track = node[2]
    label = labels[n]
    ahead[segment, track] = label

# der(head, ahead)
# 0.11199697675368721
