#!/usr/bin/env python
# encoding: utf-8

from segment import Segment
from timeline import Timeline
from comatrix import Confusion
from association import Mapping, OneToOneMapping

import numpy as np
import json

class TrackAnnotation(object):
    """    
    TrackAnnotation is a generic class for storing and accessing 
    timestamped multi-track annotations of multimedia content.
        
    * What is an annotation?
        It can be anything -- from speaker identifier, to the position
        of its mouth... The sky is the limit!
    
    * Timestamped?
        Each annotation is temporally located using a :class:`Segment`.
        Following the previous example of speaker identification, each
        segment corresponds to a speech turn.
        
    * Multi-track?
        You might want to store multiple annotations for a single segment...
        Say, for instance, there are two faces appearing during one
        shot: it is possible to annotate the shot segment with two tracks --
        one for each face. Sweeet :)
    """
    
    # =================================================================== #
    
    def __init__(self, track_class=None, video=None, modality=None, ):
        """
    Create an empty :class:`TrackAnnotation` instance.    
    
    :param track_class: the type of tracks
    :type track_class: type
    :param video: name of (or path to) annotated :attr:`video`
    :type video: string
    :param modality: name of annotated :attr:`modality`
    :type modality: string
    :rtype: :class:`TrackAnnotation`
    
    Example:
    
        The following code creates an instance A of :class:`TrackAnnotation` that is meant to store annotations
        of type **HeadPosition** and described :attr:`modality` 'head' of :attr:`video` 'MyVideo.avi'.
                
        >>> from pyannote import *
        >>> modality = 'head'
        >>> video = 'MyVideo.avi'
        >>> track_class = HeadPosition
        >>> A = TrackAnnotation(track_class, modality=modality, video=video)
        
        """
        super(TrackAnnotation, self).__init__()
        
        self.__video = video
        # __video: name of annotated video
        
        self.__modality = modality
        # __modality: name of annotated modality
        # (for instance head, speaker, spoken or written in REPERE challenge)
        
        if not isinstance(track_class, type):
            raise ValueError('Track type must be provided.')
        
        if issubclass(track_class, (int, Segment)):
            raise ValueError('Track type can be anything but int of Segment')
        
        self.__track_class = track_class
        # __track_class: type of annotated track
        # when adding a new track, its type is compared to __track_class

        self.__timeline = Timeline(video=video)
        # __timeline: 
                
        self._segment_tracks = {}
        # _segment_tracks[segment] contains a dictionary of named tracks

    # =================================================================== #

    def __get_video(self): 
        return self.__video
    def __set_video(self, value):
        self.__video = value
        self.__timeline.video = value
    video = property(fget=__get_video, \
                     fset=__set_video, \
                     fdel=None, \
                     doc="Annotated video.")
    """
    Annotated video (mutable attribute)
    
    **Usage**
    
        >>> if A.video != 'MyVideo.avi':
        ...    A.video = 'MyVideo.avi'
    """
     
    def __get_modality(self): 
        return self.__modality
    def __set_modality(self, value):
        self.__modality = value
    modality = property(fget=__get_modality, \
                        fset=__set_modality, \
                        fdel=None, \
                        doc="Annotated modality.")    
    """
    Annotated modality (mutable attribute)
    
    **Usage**
    
        >>> if A.modality != 'head':
        ...    A.modality = 'head'
    """
    
    def __get_track_class(self):
        return self.__track_class
    track_class = property(fget=__get_track_class, \
                           fset=None, \
                           fdel=None, \
                           doc="Class of tracks.")    
    """
    Class of tracks
        
    .. note:: Tracks stored in a TrackAnnotation instance must be instances of this class.
    """
    
    # =================================================================== #

    def __len__(self):
        """
    Get number of annotated segments -- **len()** operator.
        
    :rtype: int
    
    **Usage**
    
        >>> print 'There are %d annotated segments in A.' % len(A)
        """
        return len(self.__timeline)
        
    def __nonzero__(self):
        """
    Test whether annotation has at least one annotation segment (is not empty).
    
    :rtype: boolean
    
    **Usage**
    
        >>> if A:
        ...     print 'Annotation is not empty.'        
        """
        return len(self) > 0
    
    # =================================================================== #
    
    def _has_segment(self, segment):
        """
    Test whether segment is annotated -- called by __contains__()    
        """
        
        #DEBUG print  "TrackAnnotation > _has_segment"
                
        return segment in self._segment_tracks
    
    def __contains__(self, segment):
        """
    Test whether segment is annotated -- **in** operator.
    
    :rtype: boolean
    
    **Usage**
    
        >>> segment = Segment(0, 1)
        >>> if segment in A:
        ...    print 'There is at least one annotated track for segment %s.' % segment
        
    .. note::
    
        The **in** operator looks for exact segment matches. 
        Even if segment **[0 --> 3]** is annotated, asking for segment **[1 --> 2]** will return False.
    
        See :meth:`__call__` for more advanced functionalities.
        """
        return self._has_segment(segment)
    
    def _has_segment_name(self, segment, name):
        """
        Return True if any annotation with name exsits for segment
               False otherwise
        """
        
        #DEBUG print  "TrackAnnotation > _has_segment_name"
        
        return self._has_segment(segment) and \
               name in self._segment_tracks[segment]
    
    def auto_track_name(self, segment, prefix='track'):
        """
    .. currentmodule:: pyannote

    Automatically generate name for a new track on a given :data:`segment`.
    Make sure that returned name does not already exist by appending
    a number (starting at 0) at the end of :data:`prefix`.
        
    :param segment: segment to be annotated
    :type segment: :class:`Segment`
    :param prefix: track name prefix
    :type prefix: string
    :rtype: string
    
    **Example**
    
        >>> A = TrackAnnotation(int, video='MyVideo.avi', modality='audio')
        >>> print A.auto_track_name(Segment(0, 1), prefix='speaker')
        speaker0
        """
        
        # existing tracks names
        if not self._has_segment(segment):
            track_names = []
        else:
            track_names = self._get_segment(segment).keys()
        
        # find first track name available -- track0, track1, track2, ...
        count = 0
        while( '%s_%d' % (prefix, count) in track_names ):
            count += 1
        
        return '%s_%d' % (prefix, count)
        
    # =================================================================== #

    def _get_segment(self, segment):
        """
    Get tracks for segment.
    
    :param segment: segment to get tracks from
    :type segment: :class:`Segment`
    
    :rtype: dictionary of tracks {track_name: track}
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.
        """
        
        #DEBUG print  "TrackAnnotation > __get_segment"
        
        return self._segment_tracks[segment]

    def _get_segment_name(self, segment, name):
        """
    Get segment track by name.
    
    :param segment: segment to get tracks from
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    
    :rtype: track type, see :attr:`track_class`

    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.
        """
        
        #DEBUG print  "TrackAnnotation > _get_segment_name"
        
        return self._segment_tracks[segment][name]
        
    def __getitem__(self, key):
        """
    Get all tracks for a given segment:
        >>> tracks = A[segment]
        
    Get a track by its name for a given segment:
        >>> track = A[segment, name]
            
    .. note::
    
        Raises a KeyError if :data:`segment` is not annotated or if no track called :data:`name`
        exists for this :data:`segment`. 
        
        See :meth:`__call__` for more advanced functionalities.
        
        """
        
        #DEBUG print  "TrackAnnotation > __getitem__"
        
        #
        # A[segment, name]
        #
        if isinstance(key, tuple) and len(key) == 2:
            segment = key[0]
            name = key[1]
            if self._has_segment_name(segment, name):
                return self._get_segment_name(segment, name)
            else:
                if self._has_segment(segment):
                    raise KeyError('No annotation called %s for segment %s.' \
                                   % (name, segment))
                else:
                    raise KeyError('No annotation for segment %s.' % segment)
        
        #
        # A[segment]
        #
        elif isinstance(key, Segment):
            segment = key
            if self._has_segment(segment):
                return self._get_segment(key)
            else:
                raise KeyError('No annotation for segment %s.' % segment)

        #
        # A[ any other key ]
        #
        else:
            raise TypeError('')
    
    # =================================================================== #
            
    def __get_timeline(self):
        return self.__timeline
    timeline = property(fget=__get_timeline, \
                        fset=None, \
                        fdel=None, \
                        doc="Annotation timeline.")
    """
    Annotation timeline (containing all segments with at least one track)
    Read-only attribute.
    
    **Usage**
    
        >>> timeline = A.timeline
    """
    
    def __iter__(self):
        """
    Enumerate all annotated segments in chronological order
    
    **Usage**
    
        >>> for s, segment in enumerate(A):
        ...     print "Do something with segment %s." % segment
        """
        return iter(self.__timeline)

    def itertracks(self, data=False):
        for segment in self:
            for track in self._get_segment(segment):
                if data:
                    yield segment, track, self._get_segment_name(segment, track)
                else:
                    yield segment, track

    def __reversed__(self):
        """
    Enumerate all annotated segments in reversed chronological order    

    **Usage**
    
        >>> for s, segment in reversed(A):
        ...     print "Do something with segment %s." % segment
        """
        return reversed(self.__timeline)
    
    # =================================================================== #
    
    def _del_segment(self, segment):
        """
    Delete all tracks for segment (and segment) and return deleted tracks.
    
    :param segment: deleted segment
    :type segment: :class:`Segment`
    
    :rtype: dictionary of deleted tracks {track_name: track}
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.        
        """
        
        #DEBUG print  "TrackAnnotation > _del_segment"
        
        # keep a copy of the deleted tracks
        deleted_tracks = self._get_segment(segment)
        
        # this is where segment (and all its tracks) is actually deleted
        # ... from ._segment_tracks attribute
        del self._segment_tracks[segment]
        # ... from .__timeline attribute
        position = self.__timeline.index(segment)
        del self.__timeline[position]
        
        # return deleted tracks for potential future use
        return deleted_tracks
    
    def _del_segment_name(self, segment, name):
        """
    Delete track from segment by name and return deleted track.
    If segment no longer has any track, it is also deleted.
    
    :param segment: segment to delete track from
    :type segment: :class:`Segment`
    :param name: name of deleted track
    :type name: string
    
    :rtype: track type, see :attr:`track_class`

    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.    
        """
        
        #DEBUG print  "TrackAnnotation > _del_segment_name"
        
        # keep a copy of the deleted track
        deleted_track = self._get_segment_name(segment, name)
        
        # this is where track is actually deleted
        # ... from ._segment_tracks attribute 
        del self._segment_tracks[segment][name]
        
        # if segment no longer has any track
        # remove segment as well
        if not self._segment_tracks[segment]:
            self._del_segment(segment)
        
        # return deleted track for potential future use
        return deleted_track
        
    def __delitem__(self, key):
        """
    Delete all tracks for a given segment:
        >>> del A[segment]
        
    Delete a track by its name for a given segment:
        >>> del A[segment, name]
    
    If segment no longer has any track, it is also deleted.
    
    .. note::
    
        Raises a KeyError if :data:`segment` is not annotated or if no track called :data:`name`
        exists for this :data:`segment`. 
        
        """
        
        #DEBUG print  "TrackAnnotation > __delitem__"
        
        #
        # del A[segment, name]
        #
        if isinstance(key, tuple) and len(key) == 2:
            segment = key[0]
            name = key[1]
            if self._has_segment_name(segment, name):
                return self._del_segment_name(segment, name)
            else:
                if self._has_segment(segment):
                    raise KeyError('No annotation called %s for segment %s.' \
                                   % (name, segment))
                else:
                    raise KeyError('No annotation for segment %s.' % segment)
        
        #
        # del A[segment]
        #
        elif isinstance(key, Segment):
            segment = key
            if self._has_segment(segment):
                return self._del_segment(key)
            else:
                raise KeyError('No annotation for segment %s.' % segment)

        #
        # del A[ any other key ]
        #
        else:
            raise TypeError('')    
    
    # =================================================================== #
    
    def _set_segment(self, segment, tracks):
        """
    Add multiple tracks at once for segment.
    If tracks already exist for this segment, they are deleted.
    
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :type tracks: dictionary
    :param tracks: dictionary of tracks {track_name: track}
    
    :rtype: dictionary of deleted tracks {track_name: track}
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.        
        """
        
        #DEBUG print  "TrackAnnotation > _set_segment"
        
        # delete any existing annotation for segment
        if self._has_segment(segment):
            deleted_tracks = self._del_segment(segment)
        else:
            deleted_tracks = {}
            
        # segment no longer exist, we must add it again
        # only if tracks is not empty
        if tracks:
                    
            # update global timeline
            self.__timeline += segment

            # initialize ._segment_tracks[segment] (segment-to-track)
            # with empty dictionary of tracks
            self._segment_tracks[segment] = {}
        
        for name in tracks:
            track = tracks[name]
            self._segment_tracks[segment][name] = track
            
        return deleted_tracks
    
    def _set_segment_name(self, segment, name, track):
        """
    Add one track called name for segment.
    If a track with similar name already exist for this segment, it is deleted.
    
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    :type track: 
    :param track: added track
    
    :rtype: track type, see :attr:`track_class`
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.        
        """
        
        #DEBUG print  "TrackAnnotation > _set_segment_name"
        
        # delete any existing annotation called name for segment
        if self._has_segment_name(segment, name):
            deleted_track = self._del_segment_name(segment, name)
        else:
            deleted_track = None
        
        # if segment is a new one, add it
        if not self._has_segment(segment):
            
            # update global timeline
            self.__timeline += segment
             
            # initialize ._segment_tracks[segment] (segment-to-track)
            # with empty dictionary of tracks
            self._segment_tracks[segment] = {}
        
        # this is where annotation is actually added
        self._segment_tracks[segment][name] = track
        
        # return previous annotation replaced by new one
        return deleted_track
        
    def __setitem__(self, key, value):
        """
    .. currentmodule:: pyannote

    Add multiple tracks at once for a given segment:
        >>> tracks = {'first track name': track1, 
        ...           'other track name': track2, 
        ...           'final track name': track3}
        >>> A[segment] = tracks
        
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param tracks: named tracks
    :type tracks: dictionary of tracks, see :attr:`track_class`
    
    Add track called name to segment:
        >>> A[segment, name] = track

    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    :param track: track
    :type track: track class, see :attr:`track_class`

    .. note::
    
        Raises a TypeError if added tracks do not follow the track type provided in :attr:`track_class`.
        """
        
        #DEBUG print  "TrackAnnotation > __setitem__"
        
        #
        # A[segment, name] = track
        #
        if isinstance(key, tuple) and len(key) == 2:
            # parse key and value
            segment = key[0]
            name = key[1]
            track = value
            
            # make sure track has correct type
            track = value
            if not isinstance(track, self.__track_class):
                raise TypeError('Annotation must be an instance of %s -- not %s.' \
                                 % (self.__track_class.__name__, \
                                    type(track).__name__))
            
            # make sure segment is a valid non-empty segment
            if not (isinstance(segment, Segment) and segment):
                if not isinstance(segment, Segment):
                    raise KeyError('Only segments can be annotated -- not %s.' \
                     % type(segment).__name__)
                else:
                    raise KeyError('Only non-empty segments can be annotated.')
            
            # this is where annotation is actually set
            replaced_track = self._set_segment_name(segment, name, track)
            
            return replaced_track
        
        #
        # A[segment] = tracks
        #
        elif isinstance(key, Segment):
            # parse key and value
            segment = key
            tracks = value
            
            # make sure tracks has correct type
            if not isinstance(tracks, dict):
                raise TypeError('Annotation must be a dictionary of %s.' \
                                % self.__track_class.__name__)
            for name in tracks:
                track = tracks[name]
                if not isinstance(track, self.__track_class):
                    raise TypeError('Annotation %s must be an instance of %s ' \
                                    '-- not %s' % (name, \
                                                  self.__track_class.__name__, \
                                                  type(track).__name__))
            
            # make sure segment is a valid non-empty segment
            if not (isinstance(segment, Segment) and segment):
                if not isinstance(segment, Segment):
                    raise KeyError('Only segments can be annotated -- not %s.' \
                                   % type(segment).__name__)
                else:
                    raise KeyError('Only non-empty segments can be annotated.')
            
            # this is where annotation is actually set
            replaced_tracks = self._set_segment(segment, tracks)
            
            return replaced_tracks
        
        #
        # del A[ any other key ] = whatever
        #
        else:
            raise TypeError('')    
    
    # =================================================================== #
    
    def __call__(self, subset, mode='strict'):
        """
        
    .. currentmodule:: pyannote
    
    Get a subset of annotations.
    
    :param subset: :class:`Segment` or :class:`Timeline`
    :param mode: choose between 'strict', 'loose' and 'intersection'
    :rtype: :class:`TrackAnnotation`
    
    >>> a = A(segment, mode='strict' | 'loose' | 'intersection')
    
        * :data:`mode` = 'strict'
            subset :data:`a` only contains annotations of 
            segments fully included in :data:`segment`
        
        * :data:`mode` = 'loose'
            subset :data:`a` only contains annotations of 
            segments with a non-empty intersection with :data:`segment`
        
        * :data:`mode` = 'intersection'
            same as 'loose' except segments are trimmed
            down to their intersection with :data:`segment`            
        
    >>> a = A(timeline, mode='strict' | 'loose' | 'intersection')
    
        * :data:`mode` = 'strict'
            subset :data:`a` only contains annotations of 
            segments fully included in :data:`timeline` coverage
        
        * :data:`mode` = 'loose'
            subset :data:`a` only contains annotations of 
            segments with a non-empty intersection with :data:`timeline` coverage
        
        * :data:`mode` = 'intersection'
            same as 'loose' except segments are trimmed
            down to their intersection with :data:`timeline` coverage
                 
        """

        if mode == 'strict':
            sub_timeline = self.timeline(subset, mode='strict')
        elif mode in ['loose', 'intersection']:
            sub_timeline = self.timeline(subset, mode='loose')
            if mode == 'intersection':
                # note that isub_timeline might have less segments than
                # sub_timeline for some particular situation
                isub_timeline = self.timeline(subset, mode='intersection')
        else:
            raise ValueError('')

        sub_annotation = self.__class__(track_class=self.__track_class, \
                                        video=self.video, \
                                        modality=self.modality)

        for s, segment in enumerate(sub_timeline):
            tracks = self[segment]
            if mode == 'intersection':
                
                # get segment from isub_timeline that corresponds
                # to current segment from sub_timeline
                isegment = isub_timeline(segment, mode='strict')[0]
                
                # if isegment is already annotated 
                # then we might have a problem, Houston.
                if isegment in sub_annotation:
                    for name in tracks:
                        if name in sub_annotation[isegment]:
                            # MAYDAY, MAYDAY!
                            new_name = self.auto_track_name(isegment, prefix=name)
                            sub_annotation[isegment, new_name] = tracks[name]
                        else:
                            sub_annotation[isegment, name] = tracks[name]
                else:
                    sub_annotation[isegment] = tracks
            else:
                sub_annotation[segment] = tracks
        
        return sub_annotation
            
    # =================================================================== #
    
    def __rshift__(self, timeline):
        """
    Timeline tagging
        
    >>> a = A >> timeline   
        """
        new_annotation = self.__class__(track_class=self.__track_class, video=self.video, modality=self.modality)
        
        # Loop on each segment of the target timeline
        for segment in timeline:
            # Loop on each intersecting segment
            for isegment in self.timeline(segment, mode='loose'):
                # Add tracks from current intersecting segment
                tracks = self._get_segment(isegment)
                for name in tracks:
                    # If a track with similar name has already been added
                    # Generate a new name, to avoid collision
                    if new_annotation._has_segment_name(segment, name):
                        new_name = self.auto_track_name(segment, prefix=name)
                        #DEBUG print "Collision %s / %s --> %s" % (segment, name, new_name)
                        new_annotation._set_segment_name(segment, new_name, tracks[name])
                    else:
                        new_annotation._set_segment_name(segment, name, tracks[name])
        
        return new_annotation    
    
    def __abs__(self):
        """
        
    Force alignment of annotation on the partition of its own timeline.
    
    In other words, the following two lines have the same effect:
        >>> a = abs(A)
        >>> a = A >> abs(A.timeline)
        
    See :meth:`Timeline.__abs__` and :meth:`__pow__` for more details.
        """
        return self >> abs(self.timeline)

    def copy(self, map_func=None):
        """
        Generate a duplicate annotation
        
        :param map_func: map_func(segment) = other_segment
        :type map_func: function
        
        """
        cls = type(self)
        annotation = cls(track_class=self.track_class, video=self.video, modality=self.modality)
        
        if not map_func:
            map_func = lambda segment: segment
        
        for segment, track, data in self.itertracks(data=True):
            annotation._set_segment_name(map_func(segment), track, data)
        
        return annotation    

class TrackIDAnnotation(TrackAnnotation):
    """
    TrackIDAnnotation is an extension of :class:`TrackAnnotation` to store identifiers.
    
    * What is an identifier?
        It can be anything but :class:`int` or :class:`Segment`. 
        Usually, you might want to use a :class:`string` to store
        the name of a person, for instance. 
    
    * Data can be associated to each (segment, track, identifier) tuple.
        For instance, you can use the following to store some kind of probability
        for face #1 in segment to be 'Paul':
            >>> A[segment, 'face1', 'Paul'] = 0.85

    * Each track can have multiple identifiers.
        >>> A[segment, 'face1'] = {'Paul': 0.85, 'Jean': 0.23, 'Nicholas': 0.11}
    """
    
    # =================================================================== #
    
    def __init__(self, video=None, modality=None, **keywords):
        """
    Create an empty :class:`TrackIDAnnotation` instance.    
    
    :param video: name of (or path to) annotated :attr:`video`
    :type video: string
    :param modality: name of annotated :attr:`modality`
    :type modality: string
    :rtype: :class:`TrackIDAnnotation`
    
    Example:
    
        The following code creates an instance A of :class:`TrackIDAnnotation` that is meant to store 
        identifier annotations for :attr:`modality` 'head' of :attr:`video` 'MyVideo.avi'.
                
        >>> from pyannote import *
        >>> modality = 'head'
        >>> video = 'MyVideo.avi'
        >>> A = TrackIDAnnotation(modality=modality, video=video)
        
        """
        super(TrackIDAnnotation, self).__init__(track_class=dict, video=video, modality=modality)
        
        # _identifier_timeline[identifier] is a timeline 
        # made of segments where identifier has been annotated
        # _identifier_timeline.keys() can be used to get 
        # the whole list of track identifiers
        self._identifier_timeline = {}

        # _identifier_count[identifier][segment] = number of tracks with this identifier
        self._identifier_count = {}
        
    # =================================================================== #
    
    def __has_identifier(self, identifier):
        """
    Test whether there is at least one annotation with this identifier
        """
        return identifier in self._identifier_count
        
    # =================================================================== #
    
    # == INHERITED ==
    # def _has_segment(self, segment):
    # def _has_segment_name(self, segment, name):
    
    def __has_segment_name_identifier(self, segment, name, identifier):
        """
        Return True if any annotation with identifier exists for a track called name in segment
               False otherwise
        """
        
        #DEBUG print  "TrackIDAnnotation > __has_segment_name_identifier"
        
        return super(TrackIDAnnotation, self)._has_segment_name(segment, name) and \
               identifier in self._segment_tracks[segment][name]
    
    # =================================================================== #

    # == INHERITED ==
    # def _get_segment(self, segment):
    # def _get_segment_name(self, segment, name):
        
    def _get_segment_name_identifier(self, segment, name, identifier):
        """
    Get data for a given identifier/track/segment.
    
    :param segment: segment to get tracks from
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    :param identifier: identifier
    :type identifier: any valid identifier type
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.
        """
        #DEBUG print  "TrackIDAnnotation > _get_segment_name_identifier"        
        
        return self._segment_tracks[segment][name][identifier]

    def __getitem__(self, key):
        """
    Get all tracks for a given segment:
        >>> tracks = A[segment]
        
    Get a track by its name for a given segment:
        >>> track = A[segment, name]
    
    Get data for a given identifier on the track called name for a given segment
        >>> data = A[segment, name, identifier]
    
    .. note::
    
        Raises a KeyError if :data:`segment` is not annotated, if no track called :data:`name`
        exists for this :data:`segment` or if no such identifier for this track exists. 
        
        See :meth:`__call__` for more advanced functionalities.
        
        """
        #DEBUG print  "TrackIDAnnotation > __getitem__"
        
        #
        # A[segment, name, identifier]
        #
        if isinstance(key, tuple) and len(key) == 3:
            
            # get segment and check it
            segment = key[0]
            if not isinstance(segment, Segment):
                raise KeyError('')
            else:
                if not segment:
                    raise KeyError('')
            
            # get name and identifier
            name = key[1]
            identifier = key[2]
            
            if self.__has_segment_name_identifier(segment, name, identifier):
                return self._get_segment_name_identifier(segment, \
                                                          name, \
                                                          identifier)
            else:
                if self._has_segment_name(segment, name):
                    raise KeyError('No annotation with identifier %s for ' \
                                    'track %s of segment %s.' \
                                    % (name, segment, identifier))
                else:
                    if self._has_segment(segment):
                        raise KeyError('No annotation called %s for segment %s.' \
                                       % (name, segment))
                    else:
                        raise KeyError('No annotation for segment %s.' % segment)
        else:
            #
            # INHERITED: A[segment, name]
            # INHERITED: A[segment]
            #
            return super(TrackIDAnnotation, self).__getitem__(key)
    
    # =================================================================== #
    
    def __del_identifier_segment(self, identifier, segment):
        """
        Called when identifier no longer appears in segment (in any track)
        Updates ._identifier_count and ._identifier_timeline accordingly
        """
        
        #DEBUG print  "TrackIDAnnotation > __del_identifier_segment"
        
        del self._identifier_count[identifier][segment]
        i = self._identifier_timeline[identifier].index(segment)
        del self._identifier_timeline[identifier][i]
        if not self._identifier_count[identifier]:
            del self._identifier_count[identifier]
            del self._identifier_timeline[identifier]
    
    # ------------------------------------------------------------------- #    
        
    def _del_segment(self, segment):
        """
    Delete all tracks for segment (and segment) and return deleted tracks.
    
    :param segment: deleted segment
    :type segment: :class:`Segment`
    
    :rtype: dictionary of deleted tracks {track_name: track}
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.        
        """
        
        #DEBUG print  "TrackIDAnnotation > _del_segment"
        
        # keep a copy of the deleted tracks
        deleted_tracks = super(TrackIDAnnotation, self)._del_segment(segment)
        
        # get the set of deleted identifiers for segment
        deleted_identifiers = \
                 set([identifier for name in deleted_tracks for identifier in deleted_tracks[name] ])
        
        # identifier no longer appears in segment
        # internal count/timeline need to be updated
        for identifier in deleted_identifiers:
            self.__del_identifier_segment(identifier, segment)
        
        # return deleted track for potential future use
        return deleted_tracks
    
    def _del_segment_name(self, segment, name):
        """
    Delete track from segment by name and return deleted track.
    If segment no longer has any track, it is also deleted.
    
    :param segment: segment to delete track from
    :type segment: :class:`Segment`
    :param name: name of deleted track
    :type name: string
    
    :rtype: track type, see :attr:`track_class`

    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.    
        """
        
        #DEBUG print  "TrackIDAnnotation > _del_segment_name"
        
        # keep a copy of the deleted track
        deleted_track = super(TrackIDAnnotation, self)._del_segment_name(segment, name)
        
        # decrement deleted identifiers counts for this segment
        for identifier in deleted_track:
            self._identifier_count[identifier][segment] -= 1
        
        # in case identifier no longer appears in segment
        # internal count/timeline need to be updated
        for identifier in deleted_track:
            if self._identifier_count[identifier][segment] == 0:
                self.__del_identifier_segment(identifier, segment)
                
        # return deleted track for potential future use
        return deleted_track
    
    def _del_segment_name_identifier(self, segment, name, identifier):
        
        #DEBUG print  "TrackIDAnnotation > _del_segment_name_identifier"
        
        # remove identifier for this particular track in segment
        del self._segment_tracks[segment][name][identifier]
        
        # if track no longer has any identifier
        # it needs to be removed
        if not self._segment_tracks[segment][name]:
            self._del_segment_name(segment, name)
        
        # decrement deleted identifier count for this segment
        self._identifier_count[identifier][segment] -= 1
        
        # in case identifier no longer appears in segment
        # internal count/timeline need to be updated
        if self._identifier_count[identifier][segment] == 0:
            self.__del_identifier_segment(identifier, segment)

    # ------------------------------------------------------------------- #    
      
    def __delitem__(self, key):
        """
    Delete all tracks for a given segment:
        >>> del A[segment]
        
    Delete a track by its name for a given segment:
        >>> del A[segment, name]
            
    If segment no longer has any track, it is also deleted.
    
    Delete an identifier for given track and segment:
        >>> del A[segment, name, identifier]
    
    If track no longer has any segment, it is also deleted.
    
    .. note::
    
        Raises a KeyError if :data:`segment` is not annotated, if no track called :data:`name`
        exists for this :data:`segment` or if such an identifier does not exist here.
        
        """
        
        #DEBUG print  "TrackIDAnnotation > __delitem__"        
        
        #
        # del A[segment, name, identifier]
        #
        if isinstance(key, tuple) and len(key) == 3:
            segment = key[0]
            name = key[1]
            identifier = key[2]
            
            if self.__has_segment_name_identifier(segment, name, identifier):
                return self._del_segment_name_identifier(segment, \
                                                          name, \
                                                          identifier)
            else:
                raise KeyError('')
        else:
            #
            # INHERITED: del A[segment, name]
            # INHERITED: del A[segment]
            #
            super(TrackIDAnnotation, self).__delitem__(key)
    
    # =================================================================== #
    
    def __set_identifier_segment(self, identifier, segment):
        
        #DEBUG print  "TrackIDAnnotation > __set_identifier_segment"
        
        
        # add identifier if needed
        if identifier not in self._identifier_count:
            self._identifier_timeline[identifier] = Timeline(video=self.video)
            self._identifier_count[identifier] = {}

        # add segment to identifier if needed
        if segment not in self._identifier_count[identifier]:
            self._identifier_count[identifier][segment] = 0
            self._identifier_timeline[identifier] += segment
        
        # increment identifier count for this segment
        self._identifier_count[identifier][segment] += 1
    
    # ------------------------------------------------------------------- #

    def _set_segment(self, segment, tracks):
        """
    Add multiple tracks at once for segment.
    If tracks already exist for this segment, they are deleted.
    
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :type tracks: dictionary
    :param tracks: dictionary of dictionaries {track_name: track}
    
    :rtype: dictionary of deleted tracks {track_name: track}
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.        
        """
        
        #DEBUG print  "TrackIDAnnotation > _set_segment"
        
        deleted_tracks = super(TrackIDAnnotation, self)._set_segment(segment, \
                                                                 tracks)

        for name in tracks:
            track = tracks[name]
            for identifier in track:
                self.__set_identifier_segment(identifier, segment)
            
        return deleted_tracks
    
    def _set_segment_name(self, segment, name, track):
        """
    Add one track called name for segment.
    If a track with similar name already exist for this segment, it is deleted.
    
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    :type track: 
    :param track: added track
    
    :rtype: track type, see :attr:`track_class`
    
    .. note::

        Does not do any parameter checking. 
        Might raise a KeyError exception if you're not careful.        
        """
        
        #DEBUG print  "TrackIDAnnotation > _set_segment_name"
        
        deleted_track = \
             super(TrackIDAnnotation, self)._set_segment_name(segment, \
                                                          name, \
                                                          track)
        
        for identifier in track:
            self.__set_identifier_segment(identifier, segment)
        
        return deleted_track
    
    def __set_segment_name_identifier(self, segment, name, identifier, value):
        """
        """
        
        #DEBUG print  "TrackIDAnnotation > __set_segment_name_identifier"
        
        # delete existing identifier if needed
        if self.__has_segment_name_identifier(segment, name, identifier):
            self._del_segment_name_identifier(segment, name, identifier)
        
        # if segment does not exist
        if not self._has_segment(segment):
            tracks = {name: {identifier: value}}
            self._set_segment(segment, tracks)
            
        # if track does not exist
        elif not self._has_segment_name(segment, name):
            track = {identifier: value}
            self._set_segment_name(segment, name, track)
        
        # 
        else:
            self._segment_tracks[segment][name][identifier] = value
            self.__set_identifier_segment(identifier, segment)
    
    # ------------------------------------------------------------------- #
    
    def __check_identifier(self, identifier):
        """
        Make sure provided identifier is a valid one (anything but int or Segment)
        """
        if not isinstance(identifier, str):
            raise TypeError('Invalid identifier %s. Must be str.' \
                            % (type(identifier).__name__))
    
    def __setitem__(self, key, value):
        """
    .. currentmodule:: pyannote

    Add multiple tracks at once for a given segment:
        >>> tracks = {'first track name': track1, 
        ...           'other track name': track2, 
        ...           'final track name': track3}
        
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param tracks: named tracks
    :type tracks: dictionary of dictionaries {identifier: data}
    
    Add track called name to segment:
        >>> A[segment, name] = {identifier1: data1, 
                                identifier2: data2, 
                                ...}

    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    
    Add data for identifier on track called name to segment:
        >>> A[segment, name, identifier] = data
    
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param name: track name
    :type name: string
    :param identifier: identifier
    :type identifier: any valid identifier type (not :class:`int` nor :class:`Segment`)
    
    .. note::
    
        Raises a TypeError if identifier is not valid.
        """
        
        #DEBUG print  "TrackIDAnnotation > __setitem__"        
        
        #
        # A[segment, name, identifier] = track
        #
        if isinstance(key, tuple) and len(key) == 3:
            segment = key[0]
            name = key[1]
            identifier = key[2]
            self.__check_identifier(identifier)
            self.__set_segment_name_identifier(segment, name, identifier, value)
        else:
            #
            # INHERITED: A[segment, name] = value 
            # INHERITED: A[segment] = value
            #            
            return super(TrackIDAnnotation, self).__setitem__(key, value)

    # =================================================================== #
        
    def __get_IDs(self): 
        return self._identifier_count.keys()
    IDs = property(fget=__get_IDs, \
                   fset=None, \
                   fdel=None, \
                   doc="List of identifiers.")
    """
    Get list of identifiers.
    """
        
    def ids(self, segment):
        """
        Get list of identifiers for requested segment.
        """
        if segment not in self:
            return set([])
        
        identifiers = set([])
        
        # loop on all tracks
        for name in self._get_segment(segment):
            # loop on all identifiers in track
            for identifier in self._get_segment_name(segment, name):
                # only added if not met yet
                identifiers.add(identifier)
        
        return identifiers
    
    def iteritems(self, data=False):
        for segment in self:
            for track in self._get_segment(segment):
                for identifier in self._get_segment_name(segment, track):                    
                    if data:
                        yield segment, track, identifier, self._get_segment_name_identifier(segment, track, identifier)
                    else:
                        yield segment, track, identifier
        
    def __call__(self, subset, mode='strict'):
        """
        
    .. currentmodule:: pyannote
    
    Get a subset of annotations:
    
    :param subset: :class:`Segment`, :class:`Timeline` or any valid identifier
    :param mode: choose between 'strict', 'loose' and 'intersection'
    :rtype: :class:`TrackIDAnnotation`
    
    >>> a = A(segment, mode='strict' | 'loose' | 'intersection')
    
        * :data:`mode` = 'strict'
            subset :data:`a` only contains annotations of 
            segments fully included in :data:`segment`
        
        * :data:`mode` = 'loose'
            subset :data:`a` only contains annotations of 
            segments with a non-empty intersection with :data:`segment`
        
        * :data:`mode` = 'intersection'
            same as 'loose' except segments are trimmed
            down to their intersection with :data:`segment`
        
    >>> a = A(timeline, mode='strict' | 'loose' | 'intersection')
    
        * :data:`mode` = 'strict'
            subset :data:`a` only contains annotations of 
            segments fully included in :data:`timeline` coverage
        
        * :data:`mode` = 'loose'
            subset :data:`a` only contains annotations of 
            segments with a non-empty intersection with :data:`timeline` coverage
        
        * :data:`mode` = 'intersection'
            same as 'loose' except segments are trimmed
            down to their intersection with :data:`timeline` coverage
         
    >>> a = A( valid_identifier )
    >>> a = A( set_of_valid_identifiers )   
    >>> a = A( list_of_valid_identifiers )
    >>> a = A( tuple_of_valid_identifiers) 

        Subset :data:`a` only contains annotations with the provided identifier(s).
        
        :data:`mode` has no effect here. 
         """
        
        # use inherited __call__ method in case of Segment or Timeline subset
        if isinstance(subset, (Segment, Timeline)):
            A = super(TrackIDAnnotation, self).__call__(subset, mode=mode)
        
        # 
        elif isinstance(subset, (tuple, list, set)):
            
            # create new empty annotation
            cls = type(self)
            A = cls(video=self.video, modality=self.modality)
            
            for one_identifier in subset:
                
                # extract sub-annotation a for each identifier in list
                a = self(one_identifier, mode=mode)
                
                # add it all to the (previously empty) annotation A
                for segment, name, identifier, data in a.iteritems(data=True):
                    A.__set_segment_name_identifier(segment, name, identifier, data)
        
        # extract annotation for one particular identifier
        # and only these...
        else:
            cls = type(self)
            A = cls(video=self.video, modality=self.modality)
            identifier = subset
            timeline = self._identifier_timeline[identifier]
            for segment in timeline:
                tracks = self._get_segment(segment)
                for name in tracks:
                    track = tracks[name]
                    if identifier in track:
                        A.__set_segment_name_identifier(segment, name, identifier, track[identifier])
        
        return A
                
    def __mod__(self, translation):
        """
    Identifiers translation
    
    Create a copy of the annotation with identifiers translated according to :data:`translation`
    
    Identifiers with no available translation are left unchanged.
    
    :param translation: translation (see example below)
    :type translation: OneToOneMapping or dict
    :rtype: :class:`TrackIDAnnotation`
        
        >>> translation = {'Jean': 'John', 'Mathieu': 'Matthew'}
        >>> print A.IDs
        ['Jean', 'Mathieu', 'Paul']
        >>> a = A % translation
        >>> print a.IDs
        ['John', 'Matthew', 'Paul']
        
        """
        
        
        if not isinstance(translation, (dict, Mapping)):
            raise TypeError('Translation must be either dict or Mapping.')
        
        if isinstance(translation, Mapping):
            try:
                translation = OneToOneMapping.fromMapping(translation)
            except Exception, e:
                raise ValueError('Translation is not a one-to-one mapping.')
        
        cls = type(self)
        translated_annotation = cls(video=self.video, modality=self.modality)
        
        for segment, track, identifier, data in self.iteritems(data=True):
            
            if not identifier in translation or translation[identifier] is None:
                translated_identifier = identifier
            else:
                translated_identifier = translation[identifier]
                self.__check_identifier(translated_identifier)
            
            translated_annotation.__set_segment_name_identifier(segment, track, translated_identifier, data)
                
        return translated_annotation
    
    def __mul__(self, other):
        """
    Identifiers confusion
    >>> M = A * B
    
    :returns: confusion matrix :class:`Confusion`
        """
        return Confusion(self, other)    
        
    def toTrackIDAnnotation(self):
        return self.copy()
    
    def toJSON(self):
        data = []
        for segment in self:
            data.append({'start': segment.start, 'end': segment.end, 'ids': sorted(self.ids(segment))})
        return json.dumps(data, indent=4)
    
IDAnnotation_DefaultName = '@'

class IDAnnotation(TrackIDAnnotation):
    """
    :class:`IDAnnotation` is the mono-track version of  :class:`TrackIDAnnotation`.
    
    A segment can have only one track. A track still can have multiple identifiers.    
    """    
    
    def __init__(self, video=None, modality=None, **keywords):
        super(IDAnnotation, self).__init__(video=video, modality=modality)
    
    # =================================================================== #
    
    # == INHERITED ==
    # def __has_identifier(self, identifier):
    # def _has_segment(self, segment):
    # def _has_segment_name(self, segment, name):
    # def __has_segment_name_identifier(self, segment, name, identifier):
    # def _get_segment(self, segment):
    # def _get_segment_name(self, segment, name):
    # def _get_segment_name_identifier(self, segment, name, identifier):
    
    def __getitem__(self, key):
        """
    Get all identifiers for a given segment:
        >>> identifiers = A[segment]
        
    Get data for a given identifier for a given segment
        >>> data = A[segment, identifier]
    
    .. note::
    
        Raises a KeyError if :data:`segment` is not annotated or if no such identifier for this segment exists. 
        
        See :meth:`__call__` for more advanced functionalities.
        
        """
        
        #DEBUG print  "IDAnnotation > __getitem__"
        
        if isinstance(key, tuple) and len(key) == 2:
            segment = key[0]
            identifier = key[1]
            return super(IDAnnotation, self).__getitem__((segment, IDAnnotation_DefaultName, identifier))
        elif isinstance(key, Segment):
            segment = key
            tracks = super(IDAnnotation, self).__getitem__(segment)
            return tracks[IDAnnotation_DefaultName]
        else:
            raise KeyError('')
    
    # =================================================================== #
    
    # == INHERITED ==
    # def __del_identifier_segment(self, identifier, segment):
    # def _del_segment(self, segment):
    # def _del_segment_name(self, segment, name):
    # def _del_segment_name_identifier(self, segment, name, identifier):

    # ------------------------------------------------------------------- #    
      
    def __delitem__(self, key):
        """
    Delete all identifiers for a given segment:
        >>> del A[segment]
            
    Delete an identifier for a given segment:
        >>> del A[segment, identifier]
    
    If segment no longer has any identifier, it is also deleted.
    
    .. note::
    
        Raises a KeyError if :data:`segment` is not annotated, 
        or if such an identifier does not exist here.
        
        """
        
        #DEBUG print  "IDAnnotation > __delitem__"        
        
        if isinstance(key, tuple) and len(key) == 2:
            segment = key[0]
            identifier = key[1]
            return super(IDAnnotation, self).__delitem__((segment, IDAnnotation_DefaultName, identifier))
        elif isinstance(key, Segment):
            segment = key
            return super(IDAnnotation, self).__delitem__(segment)
        else:
            raise KeyError('')
    
    # =================================================================== #
    
    # == INHERITED ==
    # def __set_identifier_segment(self, identifier, segment):
    # def _set_segment(self, segment, tracks):
    # def _set_segment_name(self, segment, name, track):
    # def __set_segment_name_identifier(self, segment, name, identifier, value):
    
    # ------------------------------------------------------------------- #
    
    def __setitem__(self, key, value):
        """
    .. currentmodule:: pyannote

    Add multiple identifiers at once for a given segment:
        >>> A[segment] = {identifier1: data1, 
                          identifier2: data2, 
                           ...}

    :param segment: annotated segment
    :type segment: :class:`Segment`
    
    Add data for identifier to segment:
        >>> A[segment, identifier] = data
    
    :param segment: annotated segment
    :type segment: :class:`Segment`
    :param identifier: identifier
    :type identifier: any valid identifier type (not :class:`int` nor :class:`Segment`)
    
    .. note::
    
        Raises a TypeError if identifier is not valid.
        """
        
        #DEBUG print  "IDAnnotation > __setitem__"        
        
        if isinstance(key, tuple) and len(key) == 2:
            segment = key[0]
            identifier = key[1]
            return super(IDAnnotation, self).__setitem__((segment, IDAnnotation_DefaultName, identifier), value)
        elif isinstance(key, Segment):
            segment = key
            return super(IDAnnotation, self).__setitem__(segment, {IDAnnotation_DefaultName: value})
        else:
            raise KeyError('')
            
    def __rshift__(self, timeline):
        return self.toTrackIDAnnotation().__rshift__(timeline)
        
    def toTrackIDAnnotation(self):
        """
    .. currentmodule:: pyannote
    
    Convert :class:`IDAnnotation` object to :class:`TrackIDAnnotation`
        """
        annotation = TrackIDAnnotation(video=self.video, modality=self.modality)
        for segment in self:
            for identifier in self[segment]:
                annotation[segment, IDAnnotation_DefaultName, identifier] = self[segment, identifier]
        return annotation
        
    

            
