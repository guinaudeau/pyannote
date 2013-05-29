import os
from pyannote.parser import MDTMParser
from pyannote.parser.other.srt import SRTParser
import pyannote.algorithm.alignment.dtw
reload(pyannote.algorithm.alignment.dtw)

from pyannote.base.segment import SlidingWindow
import numpy as np
from pyannote import Timeline

tbbt = "/Volumes/Macintosh HD/Users/bredin/Data/tvseries/TheBigBangTheory"
os.chdir(tbbt)

speaker = MDTMParser().read('MakarandTapaswi/bbt_s01e01.mdtm')()
speaker = speaker.subset(set(['howard', 'leonard', 'other', 'penny', 'raj', 'sheldon']))

subtitles = SRTParser().read('TVsubtitles.net/The_Big_Bang_Theory - season 1.en/The Big Bang Theory - 1x01 - Pilot.HDTV.XOR.en.srt')()

source = speaker.get_timeline().coverage()
target = subtitles.coverage()

precision = 0.5
sw_source = SlidingWindow(duration=precision, step=precision,
                          start=source.extent().start, end=source.extent().end,
                          end_mode='loose')

sw_target = SlidingWindow(duration=precision, step=precision,
                          start=target.extent().start, end=target.extent().end,
                          end_mode='loose')


x_source = np.zeros((len(sw_source), 1))
x_target = np.zeros((len(sw_target), 1))

for segment in source:
    i, n = sw_source.segmentToRange(segment)
    for k in range(i, i+n):
        x_source[k] = 1

for segment in target:
    i, n = sw_target.segmentToRange(segment)
    for k in range(i, i+n):
        x_target[k] = 1

distance = lambda s,t: abs(s-t)
D, path = pyannote.algorithm.alignment.dtw.dtw(x_source, x_target, 2000, distance)

plt.figure()

plt.plot(x_source+1)
plt.plot(x_target-1)
for i,j in path[::10]:
    plt.plot([i,j], [0.8, 0.2], 'r')

plt.ylim(-2, 3)


x_source_rand = x_source + 0.01*np.random.random(x_source.shape)
x_target_rand = x_target + 0.01*np.random.random(x_target.shape)


plt.figure()
plt.plot(x_source_rand+1)
plt.plot(x_target_rand-1)
for i,j in path_rand[::10]:
    plt.plot([i,j], [0.8, 0.2], 'r')

plt.ylim(-2, 3)






speaker = MDTMParser().read('groundtruth/speaker.mdtm')
head = MDTMParser().read('groundtruth/head.mdtm')
uris = LSTParser().read('lists/uri.lst')
uri = uris[0]

source = speaker(uri).get_timeline().coverage()
target = head(uri).get_timeline().coverage()
extent = source.extent() | target.extent()

precision = 0.2
sw = SlidingWindow(duration=precision, step=precision,
                   start=extent.start, end=extent.end,
                   end_mode='loose')

x_source = np.zeros((len(sw), 1))
x_target = np.zeros((len(sw), 1))

for segment in source:
    i, n = sw.segmentToRange(segment)
    for k in range(i, i+n):
        x_source[k] = 1

for segment in target:
    i, n = sw.segmentToRange(segment)
    for k in range(i, i+n):
        x_target[k] = 1


distance = lambda s, t: abs(s-t)


def cost_matrix(source, target, window):
    n = len(source)
    m = len(target)
    C = np.zeros((n, m))
    for i in range(n):
        _i = i-max(0, i-window)
        i_ = min(i+window, n)-i
        x = source[i-_i:i+i_]
        for j in range(m):
            _j = j-max(0, j-window)
            j_ = min(j+window, m)-j
            _k = min(_i, _j)
            k_ = min(i_, j_)
            x = source[i-_k:i+k_]
            y = target[j-_k:j+k_]
            C[i, j] = 1. * np.sum(x == y) / (_k+k_)
    return C

D, path = pyannote.algorithm.alignment.dtw.dtw(x_source, x_target, 100, distance)

plt.figure()

plt.plot(x_source+1)
plt.plot(x_target-1)
for i,j in path[::10]:
    plt.plot([i,j], [0.8, 0.2], 'r')

plt.ylim(-2, 3)
