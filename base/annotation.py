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

UNIQUE_TRACK = '__@__'
UNIQUE_LABEL = '__@__'
DEFAULT_TRACK_PREFIX = 'track'

class Unknown(object):
    nextID = 0
    
    @classmethod
    def reset(cls):
        cls.nextID = 0
    
    @classmethod
    def next(cls):
        cls.nextID += 1
        return cls.nextID
    
    def __init__(self, format='Unknown%03d'):
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

class Annotation(object):
    """
    Annotated timeline.
    
    An annotation is 
    
    Parameters
    ----------
    multitrack : bool, optional
        whether a segment can contain multiple track (True) or not (False).
        Default is True (multi-track annotation).
    modality : string, optional
        name of annotated modality
    video : string, optional
        name of (audio or video) annotated document
    
    Returns
    -------
    annotation : Annotation
        New empty annotation
        
    Examples
    --------
        >>> annotation = Annotation(video='MyVideo')
        >>> print annotation.video
        MyVideo
    
    """
    def __init__(self, multitrack=True, video=None, modality=None):
        
        super(Annotation, self).__init__()
        
        # whether a segment can contain multiple track (True) or not (False)
        self.__multitrack = multitrack
        
        # name of annotated modality
        self.__modality = modality
        
        # path to (or any identifier of) segmented video
        self.__video = video
        
        # this timeline is meant to store annotated segments.
        # it only contains segments with at least one labelled track.
        # a segment that is no longer annotated must be removed from it.
        self.__timeline = Timeline(video=self.video)
        
        # this is where tracks and labels are actually stored.
        # it is a dictionary indexed by segments.
        # .__data[segment] is a dictionary indexed by tracks.
        # .__data[segment][track] contains the actual label.
        self.__data = {}
        
        # this is a dictionary indexed by labels.
        # .__label_timeline[label] is a timeline made of segments for which
        # there exists at least one track labelled by label.
        # when a label no longer exists, its entry must be removed.
        self.__label_timeline = {}
        
        # this is a dictionary indexed by labels
        # .__label_count[label] is a dictionary indexed by segments containing
        # at least one track labelled by label.
        # .__label_count[label][segment] contains the number of tracks labelled
        # as label in this segment. when zero, segment entry must be removed.
        self.__label_count = {}
    
    def __get_multitrack(self):
        return self.__multitrack
    multitrack = property(fget=__get_multitrack)
    """Can segments contain multiple tracks?"""
    
    def __get_video(self): 
        return self.__video
    video = property(fget=__get_video)
    """Path to (or any identifier of) annotated video
    
    Examples
    --------
        >>> annotation = Annotation(video="MyVideo.avi")
        >>> print annotation.video
        MyVideo.avi
    
    """
    
    def __get_modality(self): 
        return self.__modality
    modality = property(fget=__get_modality)
    """Name (or any identifier) of annotated modality
    
    Examples
    --------
        >>> annotation = Annotation(modality="speaker")
        >>> print annotation.modality
        speaker
    
    """
    
    def __get_timeline(self): 
        return self.__timeline.copy()
    timeline = property(fget=__get_timeline)
    """Timeline made of every annotated segments
    
    Examples
    --------
    >>> annotation = Annotation(multitrack=False, modality='speaker')
    >>> annotation[Segment(0, 10)] = 'Alice'
    >>> annotation[Segment(8, 20)] = 'Bob'
    >>> print annotation.timeline
    [
       [0 --> 10]
       [8 --> 20]
    ]
    
    """
    
    
    # Make sure provided segment is valid.
    def __valid_segment(self, segment):
        return isinstance(segment, Segment) and segment
    
    # Any hashable object can be used as a track name.
    def __valid_track(self, track):
        return isinstance(track, Hashable)
    
    # Strings or Unknown can be used as label.
    def __valid_label(self, label):
        return isinstance(label, (Unknown, str))
    
    def labels(self):
        """Global list of labels
        
        Returns
        -------
        labels : list
            Sorted list of existing labels (based on their string version)
        
        """
        return sorted(self.__label_count.keys(), key=str)
    
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
            
            >>> annotation = Annotation(multitrack=True)
            >>> segment = Segment(0, 2)
            >>> annotation[segment, 'speaker1'] = 'Bernard'
            >>> annotation[segment, 'speaker2'] = 'John'
            >>> print sorted(annotation.get_labels(segment))
            ['Bernard', 'John']
            >>> print annotation.get_labels(Segment(1, 2))
            set([])
            
        """
        
        if segment not in self:
            return set([])
        else:
            return set([self.__data[segment][track] \
                        for track in self.__data[segment]])
    
    def argmax(self, segment=None):
        """Most frequent label
        
        If `segment` is provided, argmax will return the label with longest
        intersection.
        If `segment` is None, argmax will simply return the label with longest
        overall duration.
        
        If no label intersects segment, returns None
        
        Parameters
        ----------
        segment : Segment, optional
            Section of annotation where to look for the most frequent label.
            Defaults to annotation timeline extent.
        
        Returns
        -------
        label : any existing label or None
        
        Examples
        --------
            
            >>> annotation = Annotation(multitrack=False, modality='speaker')
            >>> annotation[Segment(0, 10)] = 'Alice'
            >>> annotation[Segment(8, 20)] = 'Bob'
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
        durations = {lbl: (self.__label_timeline[lbl] & segment).duration()\
                     for lbl in self.labels()}
        
        # find the most frequent label
        label = max(durations.iteritems(), key=operator.itemgetter(1))[0]
        
        # in case all durations were zero, there is no most frequent label
        return label if durations[label] > 0 else None
    
    
    # Function used to parse key used to access annotation elements
    # eg. annotation[segment] or annotation[segment, track]
    def __parse_key(self, key):
        
        # For multi-track annotation, 
        # both segment and track name must be provided.
        if self.multitrack:
            if not isinstance(key, tuple) or len(key) != 2:
               raise KeyError("multi-track annotation, "
                              "expected 'annotation[segment, track]'")
            segment = key[0]
            track = key[1]
        
        # For mono-track annotation,
        # only segment must be provided.
        else:
            if not isinstance(key, Segment):
                raise KeyError("single-track annotation, "
                               "expected 'annotation[segment]'")
            segment = key
            # default name for unique track
            track = UNIQUE_TRACK
        
        return segment, track
    
    def __getitem__(self, key):
        """
        
        Use expression 'annotation[segment]' for single-track annotation
                   and 'annotation[segment, track]' for multi-track annotation
        
        Examples
        -------
        
            >>> annotation = Annotation(multitrack=True)
            >>> segment = Segment(0, 2)
            >>> annotation[segment, 'speaker1'] = 'Bernard'
            >>> annotation[segment, 'speaker2'] = 'John'
            >>> print annotation[segment, 'speaker1']
            Bernard
            >>> track2name = annotation[segment, :]
            >>> for track in sorted(track2name):
            ...     print '%s --> %s' % (track, track2name[track])
            speaker1 --> Bernard
            speaker2 --> John
        
        """
        
        # Parse requested key
        segment, track = self.__parse_key(key)
        
        # case 1: annotation[segment, :]
        # returns {track --> label} dictionary
        if track == slice(None,None,None):
            return dict(self.__data[segment])
        
        # case 2: annotation[segment] or annotation[segment, track]
        # returns corresponding label
        else:
            return self.__data[segment][track]
    
    def __setitem__(self, key, label):
        """Add/update label
        
        Use expression 'annotation[segment] = label' for single-track annotation
        and 'annotation[segment, track] = label' for multi-track annotation.

        Parameters
        ----------
        key : any valid key (annotation[segment] or annotation[segment, track])
        label : any valid label 
        
        Examples
        --------
        
            Add annotation
            
            >>> annotation = Annotation(multitrack=True)
            >>> segment = Segment(0, 2)
            >>> annotation[segment, 'speaker1'] = 'Bernard'
            >>> annotation[segment, 'speaker2'] = 'John'
            >>> print annotation
            [
               [0 --> 2] speaker1 : Bernard
                         speaker2 : John
            ]
            
            Update annotation
            
            >>> annotation[segment, 'speaker1'] = 'Paul'
            >>> print annotation
            [
               [0 --> 2] speaker1 : Paul
                         speaker2 : John
            ]
            
        """
        
        # Parse provided key
        segment, track = self.__parse_key(key)
        
        # Validate segment, track and label
        if not self.__valid_segment(segment):
            raise KeyError("invalid segment.")
        if not self.__valid_track(track):
            raise KeyError('invalid track name.')
        if not self.__valid_label(label):
            raise ValueError('invalid label.')
        
        # In case segment/track annotation already exists
        if segment in self.__data and \
           track in self.__data[segment]:
            
            # do nothing if provided label is the same as existing one
            if self.__data[segment][track] == label:
                return
            
            # remove existing label if provided label 
            # is different from existing one
            else:
                self.__delitem__(key)
        
        # Add segment if necessary
        if segment not in self.__timeline:
            # to global timeline
            self.__timeline += segment
            # to internal data dictionary
            self.__data[segment] = {}
        
        # Store label for segment/track
        self.__data[segment][track] = label
        
        # Create label timeline if necessary
        if label not in self.__label_timeline:
            self.__label_timeline[label] = Timeline(video=self.video)
        
        # Add segment to label timeline
        # Note: it won't be added twice if it already exists (see timeline API)
        self.__label_timeline[label] += segment
        
        # Create label count dictionary if necessary
        if label not in self.__label_count:
            self.__label_count[label] = {}
        
        # Initialize label count for provided segment if necessar
        if segment not in self.__label_count[label]:
            self.__label_count[label][segment] = 0
            
        # Increment label count for provided segment
        self.__label_count[label][segment] += 1
    
    def __delitem__(self, key):
        """Remove label
        
        Use expression 'del annotation[segment]' for single-track annotation
        and 'del annotation[segment, track]' for multi-track annotation.
        
        """
        
        # Parse provided key
        segment, track = self.__parse_key(key)
        
        # Special case: del T[segment, :]
        # delete all track labels, one after the other
        # (recursive calls to del T[segment, track])
        if track == slice(None,None,None):
            for t in self.__data[segment].keys():
                self.__delitem__((segment, t))
            return
        
        # del T[segment, track] for multi-track annotation
        # or del T[segment (, UNIQUE_TRACK)] for single-track annotation
        label = self.__data[segment][track]
        
        # Remove track from internal data for provided segment
        del self.__data[segment][track]
        
        # If segment no longer has any track
        # Remove segment as well
        if not self.__data[segment]:
            # from internal data 
            del self.__data[segment]
            # from global timeline
            del self.__timeline[segment]
        
        # Decrement label count for provided segment
        self.__label_count[label][segment] -= 1
        
        # If label count gets to zero
        if self.__label_count[label][segment] == 0:
            
            # remove segment for label count dictionary
            del self.__label_count[label][segment]
            
            # if label count dictionary is empty
            # remove label from dictionary
            if not self.__label_count[label]:
                del self.__label_count[label]
                
            # remove segment from label timeline
            del self.__label_timeline[label][segment]
            
            # if timeline is empty
            # remove label timeline as well
            if not self.__label_timeline[label]:
                del self.__label_timeline[label]
    
    def __len__(self):
        """Use expression 'len(annotation)'
        
        Equivalent to 'len(annotation.timeline)
        
        Returns
        -------
        number : int
            Number of annotated segments
        
        See Also
        --------
        Timeline.__len__
        
        """
        return len(self.__timeline)
    
    def __nonzero__(self):
        """Use expression 'if annotation'
        
        Equivalent to 'if annotation.timeline'
        
        Returns
        -------
        empty : bool
            False if annotation is empty (contains no annotated segment),
            True otherwise
        
        See Also
        --------
        Timeline.__nonzero__
        
        
        """
        return len(self.__timeline) > 0
        
    def __contains__(self, included):
        """Use expression 'included in annotation'
        
        Equivalent to 'included in annotation.timeline'
        
        Returns
        -------
        contains : bool
            True if every segment in `included` is annotated,
            False otherwise.
        
        See Also
        --------
        Timeline.__contains__
        
        """
        return included in self.__timeline
    
    def __iter__(self):
        """Sorted segment iterator
        
        See Also
        --------
        Timeline.__iter__
        
        """
        return iter(self.__timeline)

    def __reversed__(self):
        """Reverse-sorted segment iterator
        
        See Also
        --------
        Timeline.__reversed__
        
        """
        return reversed(self.__timeline)
    
    def iterlabels(self):
        """Annotation iterator
        
        Examples
        --------
            
            Iterate multi-track annotation
            
            >>> annotation = Annotation(multitrack=True)
            >>> annotation[Segment(0, 2), 'speaker1'] = 'Bernard'
            >>> annotation[Segment(0, 2), 'speaker2'] = 'John'  
            >>> annotation[Segment(3, 4), 'speaker1'] = 'Albert'
            >>> for segment, track, label in annotation.iterlabels():
            ...    print '%s.%s --> %s' % (segment, track, label)
            [0 --> 2].speaker1 --> Bernard
            [0 --> 2].speaker2 --> John
            [3 --> 4].speaker1 --> Albert
            
            Iterate single-track annotation
            
            >>> annotation = Annotation(multitrack=False)
            >>> annotation[Segment(0, 2)] = 'Bernard'
            >>> annotation[Segment(3, 4)] = 'Albert'
            >>> for segment, label in annotation.iterlabels():
            ...    print '%s --> %s' % (segment, label)
            [0 --> 2] --> Bernard
            [3 --> 4] --> Albert
        
        """
        
        # iterate through sorted segments
        for segment in self:
            
            # iterate through tracks
            for track in sorted(self.__data[segment]):
                
                # yield segment/track/label for multi-track annotation
                if self.multitrack:
                    yield segment, track, self.__data[segment][track]
                    
                # yield segment/label for single-track annotation
                else:
                    yield segment, self.__data[segment][track]
    
    def empty(self):
        """Empty copy of an annotation.
        
        See Also
        --------
        Timeline.empty
        
        Examples
        --------
            
            >>> annotation = Annotation(multitrack=True, video="MyVideo.avi")
            >>> annotation[Segment(0, 2), 'speaker1'] = 'Bernard'
            >>> annotation[Segment(0, 2), 'speaker2'] = 'John'  
            >>> annotation[Segment(3, 4), 'speaker1'] = 'Albert'
            >>> empty = annotation.empty()
            >>> print empty.video
            MyVideo.avi
            >>> print empty
            [
            ]
        
        """
        T = Annotation(multitrack=self.multitrack, \
                       video=self.video, \
                       modality=self.modality)
        return T
    
    def copy(self, segment_func=None, track_func=None, label_func=None):
        """Duplicate annotation.
        
        If `segment_func`, `track_func` or `label_func` are provided, they are 
        applied to segment, track and label before copying. 
        In a nutshell:
           copy[segment_func(s), track_func(t)] = label_func[original[s, t]]
        
        Therefore `segment_func` can be used to remove a segment,
        eg. in case segment_func(segment) is False, None or an empty Segment.
        
        Parameters
        ----------
        segment_func, track_func, label_func : function
            Segment, track and label transformation function
        
        Returns
        -------
        annotation : Annotation
            A (possibly modified) copy of the annotation
        
        Examples
        --------
            
            Extend all segments by one segment on each side
            
            >>> annotation = Annotation(multitrack=True, video="MyVideo.avi")
            >>> annotation[Segment(0, 2), 'speaker1'] = 'Bernard'
            >>> annotation[Segment(0, 2), 'speaker2'] = 'John'  
            >>> annotation[Segment(3, 4), 'speaker1'] = 'Albert'
            >>> segment_func = lambda s: 1 << s >> 1
            >>> copy = annotation.copy(segment_func=segment_func)
            >>> print copy
            [
               [-1 --> 3] speaker1 : Bernard
                          speaker2 : John
               [2 --> 5] speaker1 : Albert
            ]
            
            Only keep annotation for segment longer than 1 second,
            and reverse names
            
            >>> annotation = Annotation(multitrack=False)
            >>> annotation[Segment(0, 2)] = 'Bernard'
            >>> annotation[Segment(3, 4)] = 'Albert'
            >>> segment_func = lambda s: s if s.duration > 1 else None
            >>> label_func = lambda l: l[::-1]
            >>> copy = annotation.copy(segment_func=segment_func, \
                                       label_func=label_func)
            >>> print copy
            [
               [0 --> 2] : dranreB
            ]
        
        See Also
        --------
        Timeline.copy
        
        """
        
        # starts with an empty copy.
        T = self.empty()
        
        # If functions are not provided
        # make them pass-trough functions
        if segment_func is None:
            segment_func = lambda s: s
        if track_func is None:
            track_func = lambda t: t
        if label_func is None:
            label_func = lambda l: l
        
        if self.multitrack:
            for segment, track, label in self.iterlabels():
                new_segment = segment_func(segment)
                
                # Copy annotation only if transformed segment is valid
                # (make sure track and label are transformed as well)
                if new_segment:
                    T[new_segment, track_func(track)] = label_func(label)
        else:
            for segment, label in self.iterlabels():
                new_segment = segment_func(segment)
                
                # Copy annotation only if transformed segment is valid
                # (make sure label is transformed as well)
                if new_segment:
                    T[new_segment] = label_func(label)
        
        return T
                
    def __mod__(self, translation):
        """Translate labels
        
        Short-cut for Annotation.copy(label_func=translation)
        
        Parameters
        ----------
        translation: dict or ManyToOneMapping
        
        Returns
        -------
        translated : Annotation
            
        
        Examples
        --------
        
            >>> annotation = Annotation(multitrack=False)
            >>> annotation[Segment(0, 2)] = 'Bernard'
            >>> annotation[Segment(3, 4)] = 'Albert'
            >>> translation = {'Bernard': 'Bernie', 'Albert': 'Al'}
            >>> translated = annotation % translation
            >>> print translated
            [
               [0 --> 2] : Bernie
               [3 --> 4] : Al
            ]
        
        """
        
        if not isinstance(translation, (dict, Mapping)):
            raise TypeError("unsupported operand types(s) for '\%': "
                            "Annotation and %s" % type(translation).__name__)
        
        # translation is provided as a {'original' --> 'translated'} dict.
        if isinstance(translation, dict):
            
            # only transform labels that have an actual translation
            # stored in the provided dictionary, keep the others as they are.
            label_func = lambda x: translation[x] \
                                   if x in translation and translation[x] \
                                   else x
        
        # translation is provided as a ManyToOneMapping
        elif isinstance(translation, Mapping):
            
            try:
                translation = ManyToOneMapping.fromMapping(translation)
            except Exception, e:
                raise ValueError('expected N-to-1 mapping.')
            
            # only transform labels that actually have a mapping 
            # see ManyToOneMapping.__call__() API
            label_func = lambda x: translation(x) if translation(x) else x
        
        # perform the actual translation
        return self.copy(label_func=label_func)
    
    def anonymize(self):
        """Anonmyize labels
    
        Returns
        -------
        anonymized : :class:`Annotation`
            A copy where each label is replaced by an instance of ``Unknown``.
        
        """
        translation = {label: Unknown() for label in self.labels()} 
        return self % translation
    
    def __get_label(self, label):
        
        T = self.empty()
        
        if self.multitrack:
            for segment in self.__label_timeline[label]:
                for track in self.__data[segment]:
                    if self.__data[segment][track] == label:
                        T[segment, track] = label
        else:
            for segment in self.__label_timeline[label]:
                for track in self.__data[segment]:
                    if self.__data[segment][track] == label:
                        T[segment] = label
        
        return T
            
    def __call__(self, subset, mode='strict', invert=False):
        """Sub-annotation extraction.
        
        Use expression 'annotation(subset, ...)'
        
        If `subset` is a Segment or a Timeline, only extract segments that
        are fully included into its coverage. Set mode to 'loose' to extract
        all intersecting segments. `invert` has no effect in this case.
            
        If `subset` is a label or a label iterator, only extract tracks with
        provided labels. Set `invert` to True to extract **all but**
        provided labels. `mode` has no effect in this case.
        
        Parameters
        ----------
        subset : Segment, Timeline, any valid label or label iterator
        mode : {'strict', 'loose'}, optional
            `mode` only has effect when `subset` is a Segment or Timeline.
            Defaults to 'strict'. 
        invert : bool, optional
            `invert` only has effect when `subset` is a valid label or 
            label iterator. Defaults to False.
        
        Returns
        -------
        annotation : Annotation
            Extracted sub-annotation.
        
        Examples
        --------
        
            >>> annotation = Annotation(multitrack=True, video="MyVideo.avi")
            >>> annotation[Segment(0, 2), 'speaker1'] = 'Bernard'
            >>> annotation[Segment(0, 2), 'speaker2'] = 'John'  
            >>> annotation[Segment(3, 4), 'speaker1'] = 'John'
            >>> annotation[Segment(4, 5), 'speaker1'] = 'Albert'
            
            
            Extract sub-annotation for labels 'John' and 'Nicholas'
            
            >>> print annotation(['John', 'Nicholas'])
            [
               [0 --> 2] speaker2 : John
               [3 --> 4] speaker1 : John
            ]
            
            
            Extract sub-annotation for **all but** labels 'John' and 'Albert'
            
            >>> print annotation(['John', 'Albert'], invert=True)
            [
               [0 --> 2] speaker1 : Bernard
            ]
            
            
            Extract sub-annotation for segments fully included in [2 --> 4.5]
            
            >>> print annotation(Segment(2, 4.5), mode='strict')
            [
               [3 --> 4] speaker1 : John
            ]
            
            
            Extract sub-annotation for segments intersecting [2 --> 4.5]
            
            >>> print annotation(Segment(2, 4.5), mode='loose')
            [
               [3 --> 4] speaker1 : John
               [4 --> 5] speaker1 : Albert
            ]
        
        """
        
        if isinstance(subset, Timeline):
            timeline = subset
            
            if invert:
                raise NotImplementedError('')
            
            if mode == 'strict':
                # keep segment if it is fully included in timeline coverage
                coverage = timeline.coverage()
                segment_func = lambda s : s if coverage.covers(s) else False 
                return self.copy(segment_func=segment_func)
            elif mode == 'loose':
                # keep segment if it intersects timeline coverage
                coverage = timeline.coverage()
                segment_func = lambda s : s if (coverage & s) else False
                return self.copy(segment_func=segment_func)
            else:
                raise ValueError('unsupported mode.')
        
        # Segment subset
        # --------------
        elif isinstance(subset, Segment):
            segment = subset
            
            # --- Recursive call as a Timeline subset.            
            timeline = Timeline(video=self.video)
            timeline += segment
            return self.__call__(timeline, mode=mode, invert=invert)            
        
        # get set of labels
        elif isinstance(subset, (tuple, list, set)):
            
            # if invert, get the complementary set of labels
            # otherwise, make sure it is a set (not list or tuple)
            if invert:
                labels = set(self.labels()) - set(subset)
            else:
                labels = set(subset) & set(self.labels())
            
            T = self.empty()

            for label in labels:
                t = self.__get_label(label)
                if self.multitrack:
                    for segment, track, label in t.iterlabels():
                        T[segment, track] = label
                else:
                    for segment, label in t.iterlabels():
                        T[segment] = label
            
            return T
        
        # get one single label
        else:
            # one single label == set of one label
            return self.__call__(set([subset]), mode=mode, invert=invert)
    
    def __str__(self):
        """Human-friendly representation
        
        Examples
        --------
        
            >>> annotation = Annotation(multitrack=True, video="MyVideo.avi")
            >>> annotation[Segment(0, 2), 'speaker1'] = 'Bernard'
            >>> annotation[Segment(0, 2), 'speaker2'] = 'John'  
            >>> annotation[Segment(3, 4), 'speaker1'] = 'Albert'
            >>> print annotation
            [
               [0 --> 2] speaker1 : Bernard
                         speaker2 : John
               [3 --> 4] speaker1 : Albert
            ]
        
        """
        
        string = "[\n"
        
        if self.multitrack:
            
            previous = Segment(0, 0)
            for segment, track, label in self.iterlabels():
                
                if segment != previous:
                    previous = segment
                    string += '   %s %s : %s\n' % (previous, track, label)
                    n_spaces = len(str(previous))
                else:
                    string += '   %s %s : %s\n' % (' ' * n_spaces, track, label)
        
        else:
            
            previous = Segment(0, 0)
            for segment, label in self.iterlabels():
                if segment != previous:
                    previous = segment
                    string += '   %s : %s\n' % (previous, label)
                    n_spaces = len(str(previous))
                else:
                    string += '   %s : %s\n' % (' ' * nspaces, label)
                    
        string += "]"
        return string
            
    def new_track(self, segment, prefix=DEFAULT_TRACK_PREFIX):
        """Track name generator
        
        Parameters
        ----------
        segment : Segment
        
        prefix : str, optional
        
        
        Returns
        -------
        track : str
        
        Raises
        ------
        NotImplementedError when annotation is single-track.
        
        """
        if not self.multitrack:
            raise NotImplementedError('annotation is single-track')
            
        count = 0
        if segment in self:
            existing_tracks = set(self[segment, :])
        else:
            existing_tracks = set([])
        new_track = '%s%d' % (prefix, count)
        
        while new_track in existing_tracks:
            count += 1
            new_track = '%s%d' % (prefix, count)
        return new_track

if __name__ == "__main__":
    import doctest
    doctest.testmod()

