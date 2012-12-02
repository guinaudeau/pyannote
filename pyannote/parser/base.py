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
from pyannote.base.timeline import Timeline

class BaseTimelineParser(object):
    def __init__(self):
        super(BaseTimelineParser, self).__init__()
        
        # (uri, modality) ==> timeline
        self.reset()
    
    def __get_uris(self):
        return sorted(self.__loaded)
    uris = property(fget=__get_uris)
    """"""
    
    def _add(self, segment, uri):
        if uri not in self.__loaded:
            self.__loaded[uri] = Timeline(uri=uri)
        self.__loaded[uri] += segment
    
    def reset(self):
        self.__loaded = {}
    
    def read(self, path, uri=None, **kwargs):
        raise NotImplementedError('')
    
    def __call__(self, uri=None, **kwargs):
        """
        
        Parameters
        ----------
        uri : str, optional
            If None and there is more than one resource 
        
        Returns
        -------
        timeline : :class:`pyannote.base.timeline.Timeline`
        
        """
        
        match = dict(self.__loaded)
        
        # filter out all timelines 
        # but the ones for the requested resource
        if uri is not None:
            match = {v: timeline for v, timeline in match.iteritems()
                                 if v == uri }
        
        if len(match) == 0:
            # empty annotation
            return Timeline(uri=uri)
        elif len(match) == 1:
            return match.values()[0]
        else:
            raise ValueError('')

class BaseTextualTimelineParser(BaseTimelineParser):
    
    def __init__(self):
        super(BaseTextualTimelineParser, self).__init__()
    
    def _comment(self, line):
        raise NotImplementedError('')
    
    def _parse(self, line):
        raise NotImplementedError('')
    
    def read(self, path, uri=None, **kwargs):
        
        # defaults URI to path
        if uri is None:
            uri = path
        
        # open file and loop on each line
        fp = open(path, 'r')
        for line in fp:
            
            # strip line
            line = line.strip()
            
            # comment ?
            if self._comment(line):
                continue
            
            # parse current line
            s, v = self._parse(line)
            
            # found resource ?
            if v is None:
                v = uri
                
            # add segment
            self._add(s, v)
            
        fp.close()
        
        return self
    
    def write(self, timeline, f=sys.stdout, uri=None):
        """
        
        Parameters
        ----------
        timeline : :class:`pyannote.base.timeline.Timeline`
            Timeline
        f : file or str, optional
            Default is stdout.
        uri : str, optional
            When provided, overrides `timeline` uri attribute.
        """
        
        if uri is None:
            uri = timeline.uri
        
        if isinstance(f, file):
            self._append(timeline, f, uri)
        else:
            f = open(f, 'w')
            self._append(timeline, f, uri)
            f.close()


from pyannote.base.annotation import Annotation, Unknown

class BaseAnnotationParser(object):
    def __init__(self, multitrack):
        super(BaseAnnotationParser, self).__init__()
        self.__multitrack = multitrack
        self.reset()

    def __get_uris(self):
        return sorted(set([v for (v, m) in self.__loaded]))
    uris = property(fget=__get_uris)
    """"""
    
    def __get_modalities(self):
        return sorted(set([m for (v, m) in self.__loaded]))
    modalities = property(fget=__get_modalities)
    """"""
    
    def _add(self, segment, track, label, uri, modality):
        key = (uri, modality)
        if key not in self.__loaded:
            self.__loaded[key] = Annotation(uri=uri, modality=modality)
        if self.__multitrack:
            if track is None:
                track = self.__loaded[key].new_track(segment)
            self.__loaded[key][segment, track] = label
        else:
            self.__loaded[key][segment] = label
    
    def reset(self):
        self.__loaded = {}
    
    def read(self, path, uri=None, modality=None, **kwargs):
        raise NotImplementedError('')
    
    def __call__(self, uri=None, modality=None, **kwargs):
        """
        
        Parameters
        ----------
        uri : str, optional
            If None and there is more than one resource 
        modality : str, optional
        
        Returns
        -------
        annotation : :class:`pyannote.base.annotation.Annotation`
        
        """
        
        match = dict(self.__loaded)
        
        # filter out all annotations 
        # but the ones for the requested resource
        if uri is not None:
            match = {(v, m): ann for (v, m), ann in match.iteritems()
                                 if v == uri }
        
        # filter out all remaining annotations 
        # but the ones for the requested modality
        if modality is not None:
            match = {(v, m): ann for (v, m), ann in match.iteritems()
                                 if m == modality}
        
        if len(match) == 0:
            A = Annotation(uri=uri, modality=modality)
        elif len(match) == 1:
            A = match.values()[0]
        else:
            raise ValueError('Found more than one matching annotation: %s' % match.keys())
        
        # make sure UnknownXXXX labels are changed into Unknown objects
        labels = A.labels()
        translation = {l: Unknown() for l in A.labels() 
                                    if isinstance(l, str) and 
                                    (l[:7]=='Unknown' or l[:7]=='Inconnu'
                                     or l[:8]=='speaker#')}
        
        return A % translation

class BaseTextualAnnotationParser(BaseAnnotationParser):
    def __init__(self, multitrack):
        super(BaseTextualAnnotationParser, self).__init__(multitrack)
    
    def _comment(self, line):
        raise NotImplementedError('')
    
    def _parse(self, line):
        raise NotImplementedError('')
    
    def read(self, path, uri=None, modality=None, **kwargs):
        
        # defaults uri to path
        if uri is None:
            uri = path
        
        # open file and loop on each line
        fp = open(path, 'r')
        for line in fp:
            
            # strip line
            line = line.strip()
            
            # comment ?
            if self._comment(line):
                continue
            
            # parse current line
            s, t, l, v, m = self._parse(line)
            
            # found resource ?
            if v is None:
                v = uri
            
            # found modality ?
            if m is None or m == 'None':
                m = modality
            
            # add label
            self._add(s, t, l, v, m)
            
        fp.close()
        
        return self
    
    def _append(self, annotation, f, uri, modality):
        raise NotImplementedError('')
    
    def write(self, annotation, f=sys.stdout, uri=None, modality=None):
        """
        
        Parameters
        ----------
        annotation : :class:`pyannote.base.annotation.Annotation`
            Annotation
        f : file or str, optional
            Default is stdout.
        uri : str, optional
            When provided, overrides `annotation` uri attribute.
        modality : str, optional
            When provided, overrides `annotation` modality attribute.
        """
        
        if uri is None:
            uri = annotation.uri
        if modality is None:
            modality = annotation.modality
        
        if isinstance(f, file):
            self._append(annotation, f, uri, modality)
            f.flush()
        else:
            f = open(f, 'w')
            self._append(annotation, f, uri, modality)
            f.close()


if __name__ == "__main__":
    import doctest
    doctest.testmod()

