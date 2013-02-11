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

from segment import Segment
from timeline import Timeline
from mapping import Mapping, ManyToOneMapping
from collections import Hashable
import operator
import numpy as np
from pyannote.base import SEGMENT, TRACK, LABEL, SCORE
from pandas import MultiIndex, DataFrame, pivot_table

class Unknown(object):
    nextID = 0
    
    @classmethod
    def reset(cls):
        cls.nextID = 0
    
    @classmethod
    def next(cls):
        cls.nextID += 1
        return cls.nextID
    
    def __init__(self, format='Inconnu_%05d'):
        super(Unknown, self).__init__()
        self.ID = Unknown.next()
        self.format = format
    
    def __str__(self):
        return self.format % self.ID
    
    def __repr__(self):
        return str(self)
    
    def __hash__(self):
        return hash(self.ID)
    
    def __eq__(self, other):
        if isinstance(other, Unknown):
            return self.ID == other.ID
        else:
            return False

class AnnotationMixin(object):
    
    def _valid_segment(self, segment):
        """Check segment validity
        
        A segment is valid it is a non-empty instance of `Segment`.
        
        Parameters
        ----------
        segment : object
            Segment candidate
        
        Returns
        -------
        valid : bool
            True if segment is a non-empty instance of `Segment`.
            False otherwise.
        
        """
        return isinstance(segment, Segment) and segment
    
    def _valid_track(self, track):
        """
        Check track validity
        
        Any hashable object can be used as a track name.
        
        Parameters
        ----------
        track : object
            Track candidate
            
        Returns
        -------
        valid : bool
            True if track is hashable. False otherwise.
        """
        return isinstance(track, Hashable)
    
    def _valid_label(self, label):
        """Check label validity
        
        Any hashable object (but segment or timeline) can be used as a label.
        
        Parameters
        ----------
        label : object
            Label candidate
        
        Returns
        -------
        valid : bool
            True if track is hashable. False otherwise.
        """
        return isinstance(label, Hashable) and \
               not isinstance(label, (Segment, Timeline))
    
    def __get_timeline(self): 
        segments = set([s for s,_ in self._df.index])
        return Timeline(segments, uri=self.uri)
    timeline = property(fget=__get_timeline)
    """Timeline of annotated segments"""
    
    def __len__(self):
        """Number of annotated segments"""
        return len(set([s for s,_ in self._df.index]))
    
    def __nonzero__(self):
        """False if annotation is empty"""
        return len(self) > 0
        
    def __contains__(self, segments):
        """Check if segments are annotated
        
        Parameters
        ----------
        segments : `Segment` or `Segment` iterator
        
        Returns
        -------
        contains : bool
            True if every segment in `segments` is annotated. False otherwise.
        """
        
        if isinstance(segments, Segment):
            segments = [segments]
        
        return all([segment in self._df.index for segment in segments])
    
    def __iter__(self):
        """Iterate over sorted segments"""
        return iter(sorted(set([s for s,_ in self._df.index])))
    
    def __reversed__(self):
        """Reverse iterate over sorted segments"""
        segments = sorted(set([s for s,_ in self._df.index]))
        return reversed(segment)
    
    def itersegments(self):
        return iter(self)
    
    def itertracks(self):
        """Iterate over annotation as (segment, track) tuple"""
        
        # make sure segment/track pairs are sorted
        self._df = self._df.sort_index()
        
        for (segment, track), _ in self._df.iterrows():
            yield segment, track
    
    def crop(self, focus, mode='strict'):
        """Crop on focus
        
        Parameters
        ----------
        focus : `Segment` or `Timeline`
        
        mode : {'strict', 'loose', 'intersection'}
            In 'strict' mode, only segments fully included in focus coverage are
            kept. In 'loose' mode, any intersecting segment is kept unchanged.
            In 'intersection' mode, only intersecting segments are kept and
            replaced by their actual intersection with the focus.
        
        Returns
        -------
        cropped : same type as caller
            Cropped version of the caller containing only tracks matching
            the provided focus and mode.
        
        Remarks
        -------
        In 'intersection' mode, the best is done to keep the track names 
        unchanged. However, in some cases where two original segments are
        cropped into the same resulting segments, conflicting track names are
        modified to make sure no track is lost.
        
        """
        if isinstance(focus, Segment):
            
            return self.crop(Timeline([focus], uri=self.uri), 
                             mode=mode)
        
        elif isinstance(focus, Timeline):
            
            # timeline made of all annotated segments
            timeline = self.timeline
            
            # focus coverage
            coverage = focus.coverage()
            
            if mode in ['strict', 'loose']:
                
                # segments (strictly or loosely) included in requested coverage
                included = timeline.crop(coverage, mode=mode)
                
                # boolean array: True if row must be kept, False otherwise
                keep = [(s in included) for s,_ in self._df.index]
                
                # crop-crop
                A = self.__class__(uri=self.uri, modality=self.modality)
                A._df = self._df[keep]
                
                return A
            
            elif mode == 'intersection':
                
                # two original segments might be cropped into the same resulting
                # segment -- therefore, we keep track of the mapping
                intersection, mapping = timeline.crop(coverage, 
                                                      mode=mode, mapping=True)
                
                # create new empty annotation
                A = self.__class__(uri=self.uri, modality=self.modality)
                
                for cropped in intersection:
                    for original in mapping[cropped]:
                        for track in self.tracks(original):
                            # try to use original track name (candidate)
                            # if it already exists, create a brand new one
                            new_track = A.new_track(cropped, candidate=track)
                            # copy each value, column by column
                            for label in self._df.columns:
                                value = self._df.get_value((original, track),
                                                           label)
                                A._df = A._df.set_value((cropped, new_track), 
                                                        label, value)
                
                return A
                
        else:
            raise TypeError('')
    
    
    def tracks(self, segment):
        """Set of tracks for query segment
        
        Parameters
        ----------
        segment : `Segment`
            Query segment
            
        Returns
        -------
        tracks : set
            Set of tracks for query segment
        """
        
        try:
            df = self._df.xs(segment)
            existing_tracks = set(df.index)
            
        except Exception, e:
            existing_tracks = set([])
            
        return existing_tracks
    
    def has_track(self, segment, track):
        """Check whether a given track exists
        
        Parameters
        ----------
        segment : `Segment`
            Query segment
        track : 
            Query track
        
        Returns
        -------
        exists : bool
            True if track exists for segment
        """
        return (segment, track) in self._df.index
    
    def get_track_by_name(self, track):
        """Get all tracks with given name
        
        Parameters
        ----------
        track : any valid track name
            Requested name track
        
        Returns
        -------
        tracks : list
            List of (segment, track) tuples
        """
        try:
            segments = list(self._df.xs(track, level=1).index)
        except Exception, e:
            segments = []
        return [(s, track) for s in segments] 
    
    def copy(self):
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = self._df.copy()
        return A
    
    def retrack(self):
        """
        """
        A = self.copy()
        reindex = MultiIndex.from_tuples([(s,n) 
                                          for n,(s,_) in enumerate(A._df.index)])
        A._df.index = reindex
        return A
        
    def new_track(self, segment, candidate=None, prefix=None):
        """Track name generator
        
        Parameters
        ----------
        segment : Segment
        prefix : str, optional
        candidate : any valid track name
            
        
        Returns
        -------
        track : str
            New track name
        """
        
        # obtain list of existing tracks for segment
        existing_tracks = self.tracks(segment)
        
        # if candidate is provided, check whether it already exists
        # in case it does not, use it
        if candidate is not None:
            if candidate not in existing_tracks:
                return candidate
        
        # no candidate was provided or the provided candidate already exists
        # we need to create a brand new one
        
        # by default (if prefix is not provided)
        # use modality as prefix (eg. speaker1, speaker2, ...)
        if prefix is None:
            prefix = '' if self.modality is None else str(self.modality)
        
        # find first non-existing track name for segment
        # eg. if speaker1 exists, try speaker2, then speaker3, ...
        count = 1
        while ('%s%d' % (prefix, count)) in existing_tracks:
            count += 1
        
        # return first non-existing track name
        return '%s%d' % (prefix, count)
    
    def __str__(self):
        """Human-friendly representation"""
        if self:
            self._df = self._df.sort_index(inplace=True)
            return str(self._df)
        else:
            return ""


class Annotation(AnnotationMixin, object):
    """
    Parameters
    ----------
    uri : string, optional
        uniform resource identifier of annotated document
    modality : string, optional
        name of annotated modality
    
    Returns
    -------
    annotation : BaseAnnotation
        New empty annotation
    """
    
    @classmethod
    def from_df(cls, df, uri=None,
                         modality=None,
                         aggfunc=np.mean):
        """
        
        Parameters
        ----------
        df : DataFrame
            Must contain the following columns: 'segment', 'track' and 'label'
        uri : str, optional
            Resource identifier
        modality : str, optional
            Modality
        aggfunc : func
            Value aggregation function in case of duplicate (segment, track, 
            label) tuples
        
        Returns
        -------
        
        """
        A = cls(uri=uri, modality=modality)
        A._df = df.set_index([SEGMENT, TRACK])[[LABEL]]
        return A
    
    
    def __init__(self, uri=None, modality=None):
        super(Annotation, self).__init__()
        index = MultiIndex(levels=[[],[]], 
                           labels=[[],[]], 
                           names=[SEGMENT, TRACK])
        self._df = DataFrame(index=index)
        self.modality = modality
        self.uri = uri
    
    
    # del annotation[segment]
    # del annotation[segment, :]
    # del annotation[segment, track]
    def __delitem__(self, key):
        if isinstance(key, Segment):
            segment = key
            self._df = self._df.drop(segment, axis=0)
        elif isinstance(key, tuple) and len(key) == 2:
            segment, track = key
            self._df = self._df.drop((segment, track), axis=0)
        else:
            raise KeyError('')
    
    # label = annotation[segment, track]
    def __getitem__(self, key):
        segment, track, = key
        return self._df.get_value((segment, track), LABEL)
    
    # annotation[segment, track] = label
    def __setitem__(self, key, label):
        segment, track = key
        if not self._valid_segment(segment):
            raise KeyError('invalid segment.')
        if not self._valid_track(track):
            raise KeyError('invalid track name.')
        if not self._valid_label(label):
            raise KeyError('invalid label.')
        self._df = self._df.set_value((segment, track), LABEL, label)
    
    def empty(self):
        return self.__class__(uri=self.uri, modality=self.modality)
    
    def labels(self):
        """List of labels
        
        Returns
        -------
        labels : list
            Sorted list of existing labels
        
        Remarks
        -------
            Labels are sorted based on their string representation.
        """
        if LABEL in self._df:
            return sorted(self._df[LABEL].unique(), key=str)
        else:
            return []
    
    def get_labels(self, segment):
        """Local set of labels 
        
        Parameters
        ----------
        segment : Segment
            Segments to get label from.
        
        Returns
        -------
        labels : set
            Set of labels for `segment` if it exists, empty set otherwise.
        
        Examples
        --------
            
            >>> annotation = Annotation()
            >>> segment = Segment(0, 2)
            >>> annotation[segment, 'speaker1'] = 'Bernard'
            >>> annotation[segment, 'speaker2'] = 'John'
            >>> print sorted(annotation.get_labels(segment))
            set(['Bernard', 'John'])
            >>> print annotation.get_labels(Segment(1, 2))
            set([])
            
        """
        
        try:
            return set(self._df.ix[segment][LABEL])
        except Exception, e:
            return set([])
    
    def subset(self, labels, invert=False):
        """Annotation subset
        
        Extract annotation subset based on labels
        
        Parameters
        ----------
        labels : set
            Set of labels
        invert : bool, optional
            If invert is True, extract all but requested `labels`
        
        Returns
        -------
        subset : `Annotation`
            Annotation subset.
        """
        
        if not isinstance(labels, set):
            raise TypeError('labels must be provided as a set of labels.')
        
        if invert:
            labels = set(self.labels()) - labels
        else:
            labels = labels & set(self.labels())
        
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = self._df[self._df[LABEL].apply(lambda l: l in labels)]
        
        return A
    
    def label_timeline(self, label):
        """Get timeline for a given label
        
        Parameters
        ----------
        label : 
        
        Returns
        -------
        timeline : :class:`Timeline`
            Timeline made of all segments annotated with `label`
        
        """
        a = self._df.ix[self._df[LABEL] == label]
        segments = set([s for s,_ in a.index])
        return Timeline(segments, uri=self.uri)
    
    def label_coverage(self, label):
        return self.label_timeline(label).coverage()
    
    def label_duration(self, label):
        return self.label_timeline(label).duration()
    
    def argmax(self, segment=None, known_first=False):
        """Get most frequent label
        
        
        Parameters
        ----------
        segment : Segment, optional
            Section of annotation where to look for the most frequent label.
            Defaults to whole annotation extent.
        known_first: bool, optional
            If True, artificially reduces the duration of intersection of 
            `Unknown` labels so that 'known' labels are returned first.
        
        Returns
        -------
        label : any existing label or None
            Label with longest intersection
            
        Examples
        --------
            
            >>> annotation = Annotation(modality='speaker')
            >>> annotation[Segment(0, 10), 'speaker1'] = 'Alice'
            >>> annotation[Segment(8, 20), 'speaker1'] = 'Bob'
            >>> print "%s is such a talker!" % annotation.argmax()
            Bob is such a talker!
            >>> segment = Segment(22, 23)
            >>> if not annotation.argmax(segment):
            ...    print "No label intersecting %s" % segment
            No label intersection [22 --> 23]
        
        """
        
        # if annotation is empty, obviously there is no most frequent label
        if not self:
            return None
        
        # if segment is not provided, just look for the overall most frequent
        # label (ie. set segment to the extent of the annotation)
        if segment is None:
            segment = self.timeline.extent()
        
        # compute intersection duration for each label
        durations = {lbl: (self.label_timeline(lbl) & segment).duration()
                     for lbl in self.labels()}
        
        # artifically reduce intersection duration of Unknown labels 
        # so that 'known' labels are returned first
        if known_first:
            maxduration = max(durations.values())
            for lbl in durations.keys():
                if isinstance(lbl, Unknown):
                    durations[lbl] = durations[lbl] - maxduration
        
        # find the most frequent label
        label = max(durations.iteritems(), key=operator.itemgetter(1))[0]
        
        # in case all durations were zero, there is no most frequent label
        return label if durations[label] > 0 else None
    
    def __rshift__(self, timeline):
        """Tag a timeline
        
        Use expression 'tagged = annotation >> timeline'
        
        Shortcut for :
            >>> tagger = DirectTagger()
            >>> tagged = tagger(annotation, timeline)
        
        Parameters
        ----------
        timeline : :class:`pyannote.base.timeline.Timeline`
        
        Returns
        -------
        tagged : :class:`pyannote.base.annotation.Annotation`
            Tagged timeline - one track per intersecting label.
            
        """
        from pyannote.algorithm.tagging import DirectTagger
        if not isinstance(timeline, Timeline):
            raise TypeError('direct tagging (>>) only works with timelines.')
        return DirectTagger()(self, timeline)
    
    
    def translate(self, translation):
        """Translate labels
        
        Parameters
        ----------
        translation: dict or ManyToOneMapping
            Label translation. 
            Labels with no associated translation are kept unchanged.
            
        Returns
        -------
        translated : :class:`Annotation`
            New annotation with translated labels.
        """
        
        if not isinstance(translation, (dict, Mapping)):
            raise TypeError("unsupported operand types(s) for '\%': "
                            "Annotation and %s" % type(translation).__name__)
        
        # translation is provided as a {'original' --> 'translated'} dict.
        if isinstance(translation, dict):
            
            # only transform labels that have an actual translation
            # stored in the provided dictionary, keep the others as they are.
            translate = lambda x: translation[x] if x in translation else x
        
        # translation is provided as a ManyToOneMapping
        elif isinstance(translation, Mapping):
            
            try:
                translation = ManyToOneMapping.fromMapping(translation)
            except Exception, e:
                raise ValueError('expected N-to-1 mapping.')
            
            # only transform labels that actually have a mapping 
            # see ManyToOneMapping.__call__() API
            translate = lambda x: translation(x) if translation(x) is not None else x
        
        # create empty annotation
        translated = self.__class__(uri=self.uri, modality=self.modality)
        # translate labels
        translated._df = self._df.applymap(translate)
        
        return translated
    
    def __mod__(self, translation):
        return self.translate(translation)
    
    def anonymize(self):
        """Anonmyize labels
        
        Create a new annotation where labels are anonymized, ie. each label
        is replaced by a unique `Unknown` instance.
        
        Returns
        -------
        anonymized : :class:`Annotation`
            New annotation with anonymized labels.
        
        """
        translation = {label: Unknown() for label in self.labels()} 
        return self % translation
    
    
    def iterlabels(self):
        """Iterate over annotation as (segment, track, label) tuple"""
        
        # make sure segment/track pairs are sorted
        self._df = self._df.sort_index()
        
        for (segment, track), column in self._df.iterrows():
            yield segment, track, column[LABEL]
    
    def smooth(self):
        """Smooth annotation
        
        Create new annotation where contiguous tracks with same label are
        merged into one longer track.
        
        Returns
        -------
        annotation : Annotation
            New annotation where contiguous tracks with same label are merged
            into one long track.
        
        Remarks
        -------
            Track names are lost in the process.
        
        """
        
        A = self.__class__(uri=self.uri, modality=self.modality)
        labels = self._df[LABEL].unique()
        
        n = 0
        for label in labels:
            coverage = self.label_coverage(label)
            for segment in coverage:
                A[segment, n] = label
                n = n+1
        
        return A
    
    def __get_label(self, label):
        """Sub-annotation extraction for one label."""
        
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = self._df.ix[self._df[LABEL] == label]
        return A


class Scores(AnnotationMixin, object):
    """
    
    Parameters
    ----------
    uri : str, optional
    
    modality : str, optional
    
    Returns
    -------
    scores : `Scores`
    
    Examples
    --------
    
        >>> s = Scores(uri='video', modality='speaker')
        >>> s[Segment(0,1), 's1', 'A'] = 0.1
        >>> s[Segment(0,1), 's1', 'B'] = 0.2
        >>> s[Segment(0,1), 's1', 'C'] = 0.3
        >>> s[Segment(0,1), 's2', 'A'] = 0.4
        >>> s[Segment(0,1), 's2', 'B'] = 0.3
        >>> s[Segment(0,1), 's2', 'C'] = 0.2
        >>> s[Segment(2,3), 's1', 'A'] = 0.2
        >>> s[Segment(2,3), 's1', 'B'] = 0.1
        >>> s[Segment(2,3), 's1', 'C'] = 0.3
        
    """
    @classmethod
    def from_df(cls, df, uri=None,
                         modality=None,
                         aggfunc=np.mean):
        """
        
        Parameters
        ----------
        df : DataFrame
            Must contain the following columns: 
            'segment', 'track', 'label' and 'value'
        uri : str, optional
            Resource identifier
        modality : str, optional
            Modality
        aggfunc : func
            Value aggregation function in case of duplicate (segment, track, 
            label) tuples
        
        Returns
        -------
        
        """
        A = cls(uri=uri, modality=modality)
        A._df = pivot_table(df, values=SCORE, 
                                rows=[SEGMENT, TRACK], 
                                cols=LABEL, 
                                aggfunc=aggfunc)
        return A
    
    def __init__(self, uri=None, modality=None):
        super(Scores, self).__init__()
        
        index = MultiIndex(levels=[[],[]], 
                           labels=[[],[]], 
                           names=[SEGMENT, TRACK])
        
        self._df = DataFrame(index=index, dtype=np.float64)
        self.modality = modality
        self.uri = uri
    
    
    # del scores[segment]
    # del scores[segment, :]
    # del scores[segment, track]
    def __delitem__(self, key):
        if isinstance(key, Segment):
            segment = key
            self._df = self._df.drop(segment, axis=0)
        elif isinstance(key, tuple) and len(key) == 2:
            segment, track = key
            self._df = self._df.drop((segment, track), axis=0)
        else:
            raise KeyError('')
    
    # value = scores[segment, track, label]
    def __getitem__(self, key):
        segment, track, label = key
        return self._df.get_value((segment, track), label)
    
    def get_track_scores(self, segment, track):
        """Get all scores for a given track.
        
        Parameters
        ----------
        segment : Segment
        track : hashable
            segment, track must be a valid track
        
        Returns
        -------
        scores : dict
            {label: score} dictionary
        """
        return {l: self._df.get_value((segment, track), l) for l in self._df}
    
    # scores[segment, track, label] = value
    def __setitem__(self, key, value):
        segment, track, label = key
        if not self._valid_segment(segment):
            raise KeyError('invalid segment: %s' % repr(segment))
        if not self._valid_track(track):
            raise KeyError('invalid track name: %s' % repr(track))
        if not self._valid_label(label):
            raise KeyError('invalid label: %s' % repr(label))
        self._df = self._df.set_value((segment, track), label, value)
    
    def labels(self):
        """List of labels
        
        Returns
        -------
        labels : list
            Sorted list of existing labels
        
        Remarks
        -------
            Labels are sorted based on their string representation.
        """
        return sorted(self._df.columns, key=str)
    
    def itervalues(self):
        """Iterate over annotation as (segment, track, label, value) tuple"""
        
        # make sure segment/track pairs are sorted
        self._df = self._df.sort_index()
        
        # yield one (segment, track, label) tuple per loop
        labels = self._df.columns
        for (segment, track), columns in self._df.iterrows():
            for label in labels:
                value = columns[label]
                if np.isnan(value):
                    continue
                else:
                    yield segment, track, label, value
    
    
    def rank(self, invert=False):
        """
        
        Parameters
        ----------
        invert : bool, optional
            By default, larger scores are better.
            Set `invert` to True to indicate smaller scores are better.
        
        Returns
        -------
        rank : `Scores`
        
        """
        if invert:
            direction = 1.
        else:
            direction = -1.
        
        rank = (direction*self._df).apply(np.argsort, axis=1)\
                                    .apply(np.argsort, axis=1)
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = rank
        
        return A
        
        
    def nbest(self, n, invert=False):
        """
        
        Parameters
        ----------
        n : int
            Size of n-best list
        invert : bool, optional
            By default, larger scores are better.
            Set `invert` to True to indicate smaller scores are better.
        
        Returns
        -------
        nbest : `Scores`
            New scores where only n-best are kept. 
        
        """
        
        if invert:
            direction = 1.
        else:
            direction = -1.
        
        nbest = (direction*self._df).apply(np.argsort, axis=1)\
                                    .apply(np.argsort, axis=1) < n
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = self._df.copy()
        A._df[~nbest] = np.nan
        
        return A
    
    
    def subset(self, labels, invert=False):
        """Scores subset
        
        Extract scores subset based on labels
        
        Parameters
        ----------
        labels : set
            Set of labels
        invert : bool, optional
            If invert is True, extract all but requested `labels`
        
        Returns
        -------
        subset : `Scores`
            Scores subset.
        """
        
        if not isinstance(labels, set):
            raise TypeError('labels must be provided as a set of labels.')
        
        if invert:
            labels = set(self.labels()) - labels
        else:
            labels = labels & set(self.labels())
        
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = self._df[list(labels)]
        
        return A
    
    
    def to_annotation(self, threshold=-np.inf, posterior=False):
        """
        
        Parameters
        ----------
        threshold : float, optional
            Each track is annotated with the label with the highest score.
            Yet, if the latter is smaller than `threshold`, label is replaced
            with an `Unknown` instance.
        posterior : bool, optional
            If True, scores are posterior probabilities in open-set identification.
            If top model posterior is higher than unknown posterior, it is selected.
            Otherwise, label is replaced with an `Unknown` instance.
        """
        
        A = Annotation(uri=self.uri, modality=self.modality)
        if not self:
            return A
        
        if posterior:
            best = self.nbest(1, invert=False)
            for segment, track in self.itertracks():
                all_scores = self.get_track_scores(segment, track)
                Pu = 1.-np.sum([v for l,v in all_scores.iteritems() if not np.isnan(v)])
                best_scores = best.get_track_scores(segment, track)
                label, Pid = [(l,v) for l,v in best_scores.iteritems() if not np.isnan(v)][0]
                if Pid > Pu:
                    A[segment, track] = label
                else:
                    A[segment, track] = Unknown
        else:
            best = self.nbest(1, invert=False)
            for segment, track, label, value in best.itervalues():
                if (invert and value > threshold) or \
                   (not invert and value < threshold):
                    label = Unknown()
                A[segment, track] = label
        
        return A
    
    def map(self, func):
        """Apply function to all values"""
        A = self.__class__(uri=self.uri, modality=self.modality)
        A._df = func(self._df)
        return A
    
    

if __name__ == "__main__":
    import doctest
    doctest.testmod()

