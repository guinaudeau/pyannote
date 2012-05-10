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

import pyannote.parser

duration = 60 # 1 minute
step = 30 
output_dir = '/tmp/'
data_dir = '/Users/bredin/Data/QCompere/dryrun'
dev_or_test = 'dev'
base_dir = data_dir + '/' + dev_or_test + '/'

VIDEOS = base_dir + 'lists/dryrun.' + dev_or_test + '.txt'
UEM = base_dir + 'lists/dryrun.' + dev_or_test + '.uem'
SPEAKER = base_dir + 'manual/trs/cat.speaker.mdtm'
SPOKEN = base_dir + 'manual/trs/cat.spoken.mdtm'
HEAD = base_dir + 'manual/xgtf/cat.head.mdtm'
WRITTEN = base_dir + 'manual/xgtf/cat.written.alone.mdtm'



# ===== LOAD VIDEO LIST =====
f = open(VIDEOS, 'r')
VIDEOS = [video.strip() for video in f.readlines()]
f.close()

# ===== LOAD DATA =====
UEM = pyannote.parser.UEMParser(UEM)
SPEAKER = pyannote.parser.MDTMParser(SPEAKER)
SPOKEN = pyannote.parser.MDTMParser(SPOKEN)
HEAD = pyannote.parser.MDTMParser(HEAD)
WRITTEN = pyannote.parser.MDTMParser(WRITTEN)

f_speaker = open(output_dir + 'speaker.txt', 'w')
f_spoken = open(output_dir + 'spoken.txt', 'w')
f_head = open(output_dir + 'head.txt', 'w')
f_written = open(output_dir + 'written.txt', 'w')

for video in VIDEOS:
    
    # ==== 
    
    uem = UEM.timeline(video)
    speaker = SPEAKER.annotation(video, 'speaker')
    spoken = SPOKEN.annotation(video, 'spoken')
    head = HEAD.annotation(video, 'head')
    written = WRITTEN.annotation(video, 'written')
    
    for section in uem:
        
        sw = pyannote.base.segment.SlidingWindow(start=section.start, \
                                                 end=section.end, \
                                                 step=step, \
                                                 duration=duration)

        for window in sw:
            
            s = speaker(window, mode='intersection')
            S = spoken(window, mode='intersection')
            h = head(window, mode='intersection')
            w = written(window, mode='intersection')
        
            for segment in s:
                f_speaker.write('%s ' % " ".join(sorted(s.ids(segment))))
            f_speaker.write('\n')

            for segment in S:
                f_spoken.write('%s ' % " ".join(sorted(S.ids(segment))))
            f_spoken.write('\n')
        
            for segment in h:
                f_head.write('%s ' % " ".join(sorted(h.ids(segment))))
            f_head.write('\n')
        
            for segment in w:
                f_written.write('%s ' % " ".join(sorted(w.ids(segment))))
            f_written.write('\n')
    
f_speaker.close()
f_spoken.close()
f_head.close()
f_written.close()
        


