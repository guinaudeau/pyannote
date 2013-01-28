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
import pandas
import numpy as np
from pyannote.base.timeline import Timeline
from pyannote.base.annotation import Annotation, Scores
from pyannote.base import URI, MODALITY, SEGMENT, TRACK, LABEL, SCORE

class BaseTimelineParser(object):
    def __init__(self):
        super(BaseTimelineParser, self).__init__()
        
        # (uri, modality) ==> timeline
        self.reset()
    
    def __get_uris(self):
        return sorted(self._loaded)
    uris = property(fget=__get_uris)
    """"""
    
    def _add(self, segment, uri):
        if uri not in self._loaded:
            self._loaded[uri] = Timeline(uri=uri)
        self._loaded[uri] += segment
    
    def reset(self):
        self._loaded = {}
    
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
        
        match = dict(self._loaded)
        
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
    def __init__(self):
        super(BaseAnnotationParser, self).__init__()
        self.reset()
    
    def __get_uris(self):
        return sorted(set([v for (v, m) in self._loaded]))
    uris = property(fget=__get_uris)
    """"""
    
    def __get_modalities(self):
        return sorted(set([m for (v, m) in self._loaded]))
    modalities = property(fget=__get_modalities)
    """"""
    
    def _add(self, segment, track, label, uri, modality):
        key = (uri, modality)
        if key not in self._loaded:
            self._loaded[key] = Annotation(uri=uri, modality=modality)
        if track is None:
            track = self._loaded[key].new_track(segment)
        self._loaded[key][segment, track] = label
    
    def reset(self):
        self._loaded = {}
    
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
        
        match = dict(self._loaded)
        
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

# class BaseTextualAnnotationParser(BaseAnnotationParser):
#     
#     def __init__(self):
#         super(BaseTextualAnnotationParser, self).__init__()
#     
#     def _comment(self, line):
#         raise NotImplementedError('')
#     
#     def _parse(self, line):
#         raise NotImplementedError('')
#     
#     def read(self, path, uri=None, modality=None, **kwargs):
#         
#         # defaults uri to path
#         if uri is None:
#             uri = path
#         
#         # open file and loop on each line
#         fp = open(path, 'r')
#         for line in fp:
#             
#             # strip line
#             line = line.strip()
#             
#             # comment ?
#             if self._comment(line):
#                 continue
#             
#             # parse current line
#             s, t, l, v, m = self._parse(line)
#             
#             # found resource ?
#             if v is None:
#                 v = uri
#             
#             # found modality ?
#             if m is None or m == 'None':
#                 m = modality
#             
#             # add label
#             self._add(s, t, l, v, m)
#             
#         fp.close()
#         
#         return self
#     
#     def _append(self, annotation, f, uri, modality):
#         raise NotImplementedError('')
#     
#     def write(self, annotation, f=sys.stdout, uri=None, modality=None):
#         """
#         
#         Parameters
#         ----------
#         annotation : :class:`pyannote.base.annotation.Annotation`
#             Annotation
#         f : file or str, optional
#             Default is stdout.
#         uri : str, optional
#             When provided, overrides `annotation` uri attribute.
#         modality : str, optional
#             When provided, overrides `annotation` modality attribute.
#         """
#         
#         if uri is None:
#             uri = annotation.uri
#         if modality is None:
#             modality = annotation.modality
#         
#         if isinstance(f, file):
#             self._append(annotation, f, uri, modality)
#             f.flush()
#         else:
#             f = open(f, 'w')
#             self._append(annotation, f, uri, modality)
#             f.close()


class BaseTextualFormat(object):
    
    def get_comment(self):
        return None
    
    def get_separator(self):
        raise NotImplementedError('')
    
    def get_fields(self):
        raise NotImplementedError('')
    
    def get_segment(self, row):
        raise NotImplementedError('')
        
    def get_converters(self):
        return None
    
    def get_default_modality(self):
        return None


class BaseTextualParser(object):
    
    def __init__(self):
        super(BaseTextualParser, self).__init__()
    
    def __get_uris(self):
        return sorted(set([v for (v, m) in self._loaded]))
    uris = property(fget=__get_uris)
    """"""
    
    def __get_modalities(self):
        return sorted(set([m for (v, m) in self._loaded]))
    modalities = property(fget=__get_modalities)
    """"""
    
    def no_match(self, uri=None, modality=None):
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
        annotation : :class:`Annotation` or :class:`Scores`
        
        """
        
        match = dict(self._loaded)
        
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
            A = self.no_match(uri=uri, modality=modality)
        elif len(match) == 1:
            A = match.values()[0]
        else:
            raise ValueError('Found more than one matching annotation: %s' % match.keys())
        
        return A
    
    def comment(self, text, f=sys.stdout):
        """Add comment to a file
        
        Comment marker is automatically added in front of the text
        
        Parameters
        ----------
        text : str
            Actual comment
        f : file or str, optional
            Default is stdout.
        
        """
        comment_marker = self.get_comment()
        if comment_marker is None:
            raise NotImplementedError('Comments are not supported.')
        
        if isinstance(f, file):
            f.write('%s %s\n' % (comment_marker, text))
            f.flush()
        else:
            with open(f, 'w') as g:
                g.write('%s %s\n' % (comment_marker, text))
    
    def write(self, annotation, f=sys.stdout, uri=None, modality=None):
        """
        
        Parameters
        ----------
        annotation : `Annotation` or `Score`
            Annotation
        f : file or str, optional
            Default is stdout.
        uri, modality : str, optional
            Override `annotation` attributes
        
        """
            
        if uri is None:
            uri = annotation.uri
        if modality is None:
            modality = annotation.modality
            
        if isinstance(f, file):
            self._append(annotation, f, uri, modality)
            f.flush()
        else:
            with open(f, 'w') as g:
                self._append(annotation, g, uri, modality)
    

class BaseTextualAnnotationParser(BaseTextualParser):
    
    def read(self, path, modality=None, **kwargs):
        """
        
        Parameters
        ----------
        path : str
        
        modality : str, optional
            Force all entries to be considered as coming from this modality.
            Only taken into account when file format does not provide
            any field related to modality (e.g. .seg files)
        
        """
        
        names = self.get_fields()
        
        converters = self.get_converters()
        if converters is None:
            converters = {}
        if LABEL not in converters:
            converters[LABEL] = lambda x: x
        
        # load whole file
        df = pandas.read_table(path, header=None, 
                               sep=self.get_separator(), 
                               names=names,
                               comment=self.get_comment(),
                               converters=converters)
        
        # remove comment lines 
        # (i.e. lines for which all fields are either None or NaN)
        keep = [not all([pandas.isnull(r[n]) for n in names]) for _,r in df.iterrows()]
        df = df[keep]
        
        # add unique track numbers if they are not read from file
        if TRACK not in names:
            df[TRACK] = range(df.shape[0])
        
        # add 'segment' column build from start time & duration
        df[SEGMENT] = [self.get_segment(row) for r, row in df.iterrows()]
        
        # obtain list of resources
        uris = list(df[URI].unique())
        
        # add modality column in case it does not exist
        if MODALITY not in df:
            if modality is None:
                modality = self.get_default_modality()
            df[MODALITY] = modality if modality is not None else ""
        
        # obtain list of modalities
        modalities = list(df[MODALITY].unique())
        
        self._loaded = {}
        
        # loop on resources
        for uri in uris:
            
            # filter based on resource
            df_ = df[df[URI] == uri]
            
            # loop on modalities
            for modality in modalities:
                
                # filter based on modality
                df__ = df_[df_[MODALITY] == (modality if modality is not None else "")]
                
                a = Annotation.from_df(df__, modality=modality,
                                             uri=uri)
                
                self._loaded[uri, modality] = a
        
        return self
    
    def no_match(self, uri=None, modality=None):
        return Annotation(uri=uri, modality=modality)


class BaseTextualScoresParser(BaseTextualParser):
    
    def read(self, path, modality=None, **kwargs):
        
        names = self.get_fields()
        
        converters = self.get_converters()
        if converters is None:
            converters = {}
        if LABEL not in converters:
            converters[LABEL] = lambda x: x
        
        # load whole file
        df = pandas.read_table(path, header=None, 
                               sep=self.get_separator(), 
                               names=names,
                               comment=self.get_comment(),
                               converters=converters)
        
        # remove comment lines 
        # (i.e. lines for which all fields are either None or NaN)
        keep = [not all([pandas.isnull(r[n]) for n in names]) for _,r in df.iterrows()]
        df = df[keep]
        
        # add 'segment' column build from start time & duration
        df[SEGMENT] = [self.get_segment(row) for r, row in df.iterrows()]
        
        # add unique track number per segment if they are not read from file
        if TRACK not in names:
            s2t = {s: t for t,s in enumerate(df[SEGMENT].unique())}
            df[TRACK] = [s2t[s] for s in df[SEGMENT]]
        
        # add modality column in case it does not exist
        if MODALITY not in df:
            if modality is None:
                modality = self.get_default_modality()
            df[MODALITY] = modality if modality is not None else ""
        
        # remove all columns but those six
        df = df[[URI, MODALITY, SEGMENT, TRACK, LABEL, SCORE]]
        
        # obtain list of resources
        uris = list(df[URI].unique())
        
        # obtain list of modalities
        modalities = list(df[MODALITY].unique())
        
        self._loaded = {}
        
        # loop on resources
        for uri in uris:
            
            # filter based on resource
            df_ = df[df[URI] == uri]
            
            # loop on modalities
            for modality in modalities:
                
                # filter based on modality
                df__ = df_[df_[MODALITY] == (modality if modality is not None else "")]
                
                s = Scores.from_df(df__, modality=modality,
                                         uri=uri)
                
                self._loaded[uri, modality] = s
        
        return self
    
    def no_match(self, uri=None, modality=None):
        return Scores(uri=uri, modality=modality)


if __name__ == "__main__":
    import doctest
    doctest.testmod()

