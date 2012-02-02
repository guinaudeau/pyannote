#!/usr/bin/env python
# encoding: utf-8

def sample():
    import os.path
    sample_idx = '%s/data/sample.idx' % (os.path.dirname(__file__))
    return IDXParser(sample_idx)

class IDXParser(object):
    def __init__(self, path2idx):
        super(IDXParser, self).__init__()
        self.path2idx = path2idx
        
        # load idx file as is.
        self._time = {}
        f = open(self.path2idx, 'r')
        for line in f:
            # sample line:
            # 13 P     125911    0.384
            # f0 f1    f2        f3
            fields = line.split()
            idx = int(fields[0])
            sec = float(fields[3])
            self._time[idx] = sec
        f.close()
        
        # # fix it.
        # m = min(self._time)
        # M = max(self._time)
        # for idx in range(m+1, M-1):
        #     if (idx not in self._time) or (self._time[idx] < self._time[idx-1]):
        #         self._time[idx] = .5 * (self._time[idx-1] + self._time[idx+1])
    
    def __getitem__(self, idx):
        return self._time[idx]
    
