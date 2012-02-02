#!/usr/bin/env python
# encoding: utf-8

from segment import Segment
from timeline import Timeline
import numpy as np

class TrackAnnotation(object):
    """
    # Create annotation for video 'video' on modality 'modality'
    # Tracks must be instances of class TrackClass
    A = TrackAnnotation(TrackClass, modality='modality', 
                                  video='video')
    
    # Add new track named name to segment
    segment = Segment( start_time, end_time )
    name = 'track name'
    track = TrackClass( args )    
    A[segment, name] = track
    
    # Add multiple new named tracks to segment
    named_tracks = {'first track name': track1, 
                    'other track name': track2, 
                    'final track name': track3}
    A[segment] = named_tracks
    
    # Get just added track back
    track = A[segment, name]
    
    # Get all tracks for segment
    # as a dictionary {'name': track}
    tracks = A[segment]
    
    # Remove just added track
    del A[segment, name]
    
    # Remove all tracks for segment
    del A[segment]

    # Remove all tracks for all segments
    A.clear()
    
    # Iterate through segments
    for s, segment in enumerate(A):
        # do something with A and segment
        pass
        
    A(segment)
    A(timeline)
    
    A ** timeline
    abs(A)
    
    """
    
    # =================================================================== #
    
    def __init__(self, track_class=None, video=None, modality=None, ):
        """
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

    def __get__video(self): 
        return self.__video
    def __set__video(self, value):
        self.__video = value
        self.__timeline.video = value
    video = property(fget=__get__video, \
                     fset=__set__video, \
                     fdel=None, \
                     doc="Annotated video.")
     
    def __get__modality(self): 
        return self.__modality
    def __set__modality(self, value):
        self.__modality = value
    modality = property(fget=__get__modality, \
                        fset=__set__modality, \
                        fdel=None, \
                        doc="Annotated modality.")        
    
    # =================================================================== #

    def __len__(self):
        """
        Return number of annotated segments
        Use the expression 'len(annotation)'
        """
        return len(self.__timeline)
        
    def __nonzero__(self):
        """
        Return True if annotation is not empty, False otherwise.
        Use the expression 'if annotation'
        """
        return len(self) > 0
    
    # =================================================================== #
    
    def _has_segment(self, segment):
        """
        Return True if any annotation exists for segment
               False otherwise
        """
        
        #DEBUG print  "TrackAnnotation > _has_segment"
                
        return segment in self._segment_tracks
    
    def __contains__(self, segment):
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
        
        # existing tracks names
        if not self._has_segment(segment):
            track_names = []
        else:
            track_names = self._get_segment(segment).keys()
        
        # find first track name available -- track0, track1, track2, ...
        count = 0
        while( '%s%d' % (prefix, count) in track_names ):
            count += 1
        
        return '%s%d' % (prefix, count)
        
    # =================================================================== #

    def _get_segment(self, segment):
        """
        Return name --> track dictionary for segment
        Note: raises an error if segment does not exist
        """
        
        #DEBUG print  "TrackAnnotation > __get_segment"
        
        return self._segment_tracks[segment]

    def __get_segment_name(self, segment, name):
        """
        Return track called name for segment
        Note: raises an error if track does not exist
        """
        
        #DEBUG print  "TrackAnnotation > __get_segment_name"
        
        return self._segment_tracks[segment][name]
        
    def __getitem__(self, key):
        """
        A[segment, name]
        A[segment]
        
        """
        
        #DEBUG print  "TrackAnnotation > __getitem__"
        
        #
        # A[segment, name]
        #
        if isinstance(key, tuple) and len(key) == 2:
            segment = key[0]
            name = key[1]
            if self._has_segment_name(segment, name):
                return self.__get_segment_name(segment, name)
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

    def __iter__(self):
        return iter(self.__timeline)

    def __reversed__(self):
        return reversed(self.__timeline)
    
    # =================================================================== #
    
    def _del_segment(self, segment):
        """
        Delete segment and return corresponding tracks
        Note: raises an error if segment does not exist
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
        Delete track called name for segment and return it
        If segment no longer has any annotation, delete segment as well
        Note: raises an error if track does not exist
        """
        
        #DEBUG print  "TrackAnnotation > _del_segment_name"
        
        # keep a copy of the deleted track
        deleted_track = self.__get_segment_name(segment, name)
        
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
        Remove all annotations for segment: del A[segment]
        Remove annotation called name for segment: del A[segment, name]
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
        # Add new track named name to segment
        $ segment = Segment( start_time, end_time )
        $ name = 'track name'
        $ track = TrackClass( args )    
        $ A[segment, name] = track
    
        # Add multiple new named tracks to segment
        $ named_tracks = {'first track name': track1, 
                          'other track name': track2, 
                          'final track name': track3}
        $ A[segment] = named_tracks
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
    
    def __call__(self, requested, mode='strict'):
        """
        # Create sub-annotation. Default mode is 'loose'.
        # ... made of segments fully included in requested segment
        sub_annotation = ann(requested_segment, mode='strict')
    
        # ... made of segments with non-emtpy intersection with requested segment 
        sub_annotation = ann(requested_segment, mode='loose')
    
        # ... same as loose, except segments that are not fully included 
        #     in requested segment are trimmed to be fully included 
        sub_annotation = ann(requested_segment, mode='intersection')
    
        # ... made of segments fully included in requested timeline coverage
        #     i.e. tl(timeline, mode) == tl(timeline.coverage(), mode)  
        sub_annotation = ann(timeline, mode='strict')
    
        # ... made of segments with non-empty intersection with requested timeline coverage
        sub_annotation = ann(timeline, mode='loose')
    
        # ... same as loose, excepet segments that are not fully included
        #     in requested timeline coverage are trimmed to be fully included 
        sub_annotation = ann(timeline, mode='intersection')
        """
        
        if mode == 'strict':
            sub_timeline = self.timeline(requested, mode='strict')
        elif mode in ['loose', 'intersection']:
            sub_timeline = self.timeline(requested, mode='loose')
            if mode == 'intersection':
                isub_timeline = self.timeline(requested, mode='intersection')
        else:
            raise ValueError('')

        sub_annotation = self.__class__(self.__track_class, \
                                        video=self.video, \
                                        modality=self.modality)
                                                 
        for s, segment in enumerate(sub_timeline):
            tracks = self[segment]
            if mode == 'intersection':
                isegment = isub_timeline[s]
                sub_annotation[isegment] = tracks
            else:
                sub_annotation[segment] = tracks
        
        return sub_annotation
            
    # =================================================================== #

    def __pow__(self, timeline, modulo=None):
        """
        annotation ** timeline
        """
        
        new_annotation = self.__class__(track_class=self.__track_class, video=self.video, modality=self.modality)
        
        original_timeline = self.timeline
        S_start = 0
        N = len(original_timeline)
        
        # for each segment in new timeline
        for ns, new_segment in enumerate(timeline):
            
            original_start_segment = original_timeline[S_start]
            
            # if start segment is strictly after new segment, jump to next new segment
            if (original_start_segment > new_segment) and (original_start_segment ^ new_segment):
                continue
            
            # update start segment
            for s in range(S_start, N):
                
                original_segment = original_timeline[s]
                
                # found first intersecting segment
                if original_segment & new_segment:
                    S_start = s
                    break
                # went one step too far
                if (original_segment > new_segment):
                    break
                
                S_start = s
            
            for s in range(S_start, N):
                original_segment = original_timeline[s]
                if original_segment & new_segment:
                    for track in self[original_segment]:
                        new_annotation[new_segment] = self[original_segment]
                elif original_segment > new_segment:
                    break
                        
        return new_annotation
        

    def __abs__(self):
        """
        abs(annotation) = annotation ** abs(annotation.timeline)
        """
        return self ** abs(self.timeline)
        

def __check_identifier(identifier):
    if isinstance(identifier, (int, Segment)):
        raise TypeError('Cannot add annotation with %s identifier' \
                        % (type(identifier).__name__))

class TrackIDAnnotation(TrackAnnotation):
    """
    
    A[segment, name, identifier] = data
    A[segment, name] = data_dict
    A[segment] = track_dict

    del A[segment, name, identifier]
    del A[segment, name]
    del A[segment]
    
    data = A[segment, name, identifier]
    data_dict = A[segment, name]
    track_dict = A[segment]
    
    A.IDs
    
    A(identifier)
    A(segment,  mode='strict | loose | intersection')
    A(timeline, mode='strict | loose | intersection')
    
    B = A % translation
    
    
    """
    
    # =================================================================== #
    
    def __init__(self, video=None, modality=None, **keywords):
        """
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
        Return True if identifier is somewhere at least once
               False otherwise
        """
        return identifier in self._identifier_count
        
    # =================================================================== #
    
    # == INHERITED ==
    # def _has_segment(self, segment):
    # def _has_segment_name(self, segment, name):
    
    def __has_segment_name_identifier(self, segment, name, identifier):
        
        #DEBUG print  "TrackIDAnnotation > __has_segment_name_identifier"
        
        return super(TrackIDAnnotation, self)._has_segment_name(segment, name) and \
               identifier in self._segment_tracks[segment][name]
    
    # =================================================================== #

    # == INHERITED ==
    # def _get_segment(self, segment):
    # def __get_segment_name(self, segment, name):
        
    def __get_segment_name_identifier(self, segment, name, identifier):
        
        #DEBUG print  "TrackIDAnnotation > __get_segment_name_identifier"        
        
        return self._segment_tracks[segment][name][identifier]
        
    def __getitem__(self, key):
        """
        A[segment, name, identifier]
        INHERITED: A[segment, name]
        INHERITED: A[segment]
        
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
                return self.__get_segment_name_identifier(segment, \
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
        Delete segment
        Note: raises an error if segment does not exist
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
        Delete track called name for segment and return it
        If segment no longer has any annotation, delete segment as well
        Note: raises an error if track does not exist
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
        del A[segment, name, identifier]
        INHERITED: del A[segment, name]
        INHERITED: del A[segment]
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
    
    def __setitem__(self, key, value):
        """
        # Add new track named name to segment
        $ segment = Segment( start_time, end_time )
        $ name = 'track name'
        $ track = TrackClass( args )    
        $ A[segment, name] = track
    
        # Add multiple new named tracks to segment
        $ named_tracks = {'first track name': track1, 
                          'other track name': track2, 
                          'final track name': track3}
        $ A[segment] = named_tracks
        """
        
        #DEBUG print  "TrackIDAnnotation > __setitem__"        
        
        #
        # A[segment, name, identifier] = track
        #
        if isinstance(key, tuple) and len(key) == 3:
            segment = key[0]
            name = key[1]
            identifier = key[2]
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
    

    def __call__(self, requested, mode='strict'):
        
        if self.__has_identifier(requested):
            identifier = requested
            timeline = self._identifier_timeline[identifier]
            sub_annotation = self.__class__(video=self.video, modality=self.modality)
            for segment in timeline:
                tracks = self._get_segment(segment)
                for name in tracks:
                    track = tracks[name]
                    if identifier in track:
                        sub_annotation.__set_segment_name_identifier(segment, name, identifier, track[identifier])
        else:
            sub_annotation = super(TrackIDAnnotation, self).__call__(requested, mode=mode)
        
        return sub_annotation
        
    
    def __mod__(self, translation):
        """annotation % translation"""
        
        print type(self)
        
        translated_annotation = self.__class__(video=self.video, modality=self.modality)
        for segment in self:
            tracks = self._get_segment(segment)
            for name in tracks:
                track = tracks[name]
                for identifier in track:
                    if identifier in translation:
                        translated_identifier = translation[identifier] 
                    translated_annotation.__set_segment_name_identifier(segment, name, translated_identifier, track[identifier])
        return translated_annotation
    
    
IDAnnotation_DefaultName = '@'

class IDAnnotation(TrackIDAnnotation):
    
    def __init__(self, video=None, modality=None, **keywords):
        super(IDAnnotation, self).__init__(video=video, modality=modality)
    
    # =================================================================== #
    
    # == INHERITED ==
    # def __has_identifier(self, identifier):
    # def _has_segment(self, segment):
    # def _has_segment_name(self, segment, name):
    # def __has_segment_name_identifier(self, segment, name, identifier):
    # def _get_segment(self, segment):
    # def __get_segment_name(self, segment, name):
    # def __get_segment_name_identifier(self, segment, name, identifier):
    
    def __getitem__(self, key):
        """
        A[segment, identifier]
        A[segment]
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
        del A[segment, identifier]
        del A[segment]
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
        A[segment, identifier] = value
        A[segment] = values
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
            
            
    def __mod__(self, translation):
        """annotation % translation"""
        return super(IDAnnotation, self).__mod__(translation)
        

    
    
    
    

            
