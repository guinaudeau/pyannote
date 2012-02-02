#!/usr/bin/env python
# encoding: utf-8

from segment import Segment, RevSegment, SEGMENT_PRECISION
    
class Timeline(object):
    """
    A timeline is a collection of (possibly overlapping) segments.
    
    :param segments: how timeline should be initialized
    :type segments: list of Segments
    :param video: name of (audio or video) document segmented by this timeline
    :type video: string
    :rtype: timeline

    """
    # ----------------------------- #
    # Create timeline/ Add segments #
    # ----------------------------- #
    
    def __init__(self, segments=None, video=None):
        super(Timeline, self).__init__()
        self.__video = video
        self.__segments = [] # contains segments sorted by start time
        self.__rsegments = [] # contains segments sorted by end time
        if segments is not None:
            # add unique segment to timeline
            if isinstance(segments, Segment):
                self += segments
            # add list/set of segments to timeline
            elif isinstance(segments, list) or isinstance(segments, set):
                for s, segment in enumerate(segments):
                    self += segment
            # cannot initialize with anything but segments
            else:
                raise TypeError("timelines must be initialized with list of Segment, not %s" % (type(segments).__name__))
    
    # =================================================================== #
    
    def __get_video(self): 
        return self.__video
    def __set_video(self, value):
        self.__video = value
    video = property(fget=__get_video, \
                     fset=__set_video, \
                     fdel=None, \
                     doc="Segmented video.")
    """Path to (or name of) segmented video"""
    
    # =================================================================== #
            
    def __searchsorted_helper(self, segment, listOfSegments, left, right):
        if (left+1) >= right:
            return right
        mid = (left+right)/2
        if segment < listOfSegments[mid]:
            return self.__searchsorted_helper(segment, listOfSegments, left, mid)
        else:
            return self.__searchsorted_helper(segment, listOfSegments, mid, right)
    
    def __searchsorted(self, segment, listOfSegments):
        """
        Find index into sorted list of segments such that, if segment was inserted before
        the index, the order of the list of segments would be preserved.
        """
        # empty timeline
        if len(listOfSegments) == 0:
            return 0
        # earliest segment so far
        if segment < listOfSegments[0]:
            return 0
        # latest segment so far
        if segment > listOfSegments[-1]:
            return len(listOfSegments)
        # somewhere in the middle
        # return self.__interpolation_searchsorted_helper(segment, listOfSegments, 0, len(self))    
        return self.__searchsorted_helper(segment, listOfSegments, 0, len(self))    
    
    # =================================================================== #
    
    def __iadd__(self, other):
        """Add segments to timeline
        
        
        tl.__iadd__(other) <==> tl += other
        
        Add Segment or Timeline to an existing timeline.
        
        other : Segment or Timeline
            Segment is added to the timeline if and only if it is not empty
            and it is not already contained by the timeline
            Timeline segments are added to the timeline the one after the other
            with the same conditions as above.
        
        """
        if isinstance(other, Segment):
            if other and (other not in self.__segments):
                # TODO: make this second test faster
                
                # where should it be inserted?
                index = self.__searchsorted(other, self.__segments)
                rehto = RevSegment(other)
                xedni = self.__searchsorted(rehto, self.__rsegments)
                # actually add it
                self.__segments.insert(index, other)
                self.__rsegments.insert(xedni, rehto)
        elif isinstance(other, Timeline):
            if self.video != other.video:
                raise ValueError('Conflicting videos (%s vs. %s)' % (self.video, other.video))
            for s, segment in enumerate(other):
                self += segment
        else:
            raise TypeError("Only segments or timelines can be \
                             added to a timeline, not %s" % (type(other).__name__))
        return self
    
    def __add__(self, other):
        """
        tl.__add__(other) <==> tl + other
        
        Return a new timeline by combining all segments.
        
        other : Segment or Timeline
        
        """
        timeline = Timeline(video=self.video)
        timeline += self
        timeline += other
        return timeline
    
    # =================================================================== #
    
    def __len__(self):
        """
        tl.__len__() <==> len(tl)
        
        Return number of segments in timeline
        Use the expression 'len(timeline)'
        """
        return len(self.__segments)
        
    def __nonzero__(self):
        """
        Return True if timeline is not empty, False otherwise.
        Use the expression 'if timeline'
        """
        return len(self) > 0
    
    def extent(self):
        """
   Get timeline extent
   
   The extent of a timeline is the (unique) segment of minimum duration 
   containing all segments in timeline.

   :rtype: Segment
        """
        
        if self:
            start_time = self.__segments[0].start
            end_time   = self.__rsegments[-1].end
            return Segment(start=start_time, end=end_time)
        else:
            return Segment()        
    
    # ------------------------------------------------------------------- #
    
    def __iter__(self):
        """self.__iter__() <==> enumerate(self)"""
        return iter(self.__segments)
    
    def __reversed__(self):
        """self.__reversed__() <==> reversed(self)"""
        return reversed(self.__segments)
    
    # ------------------------------------------------------------------- #

    def coverage(self):
        """
        Return timeline with the minimum number of segments
        that covers exactly the same time span
        
        
        """
        new_timeline = Timeline(video=self.video)
        
        # if timeline is empty, coverage is empty
        if not self:
            return new_timeline
        
        new_segment = self[0]
        for segment in self[1:]:
            # if there is no gap between them
            if not (segment ^ new_segment):
                # augment current segment
                new_segment |= segment
            else:
                # add current segment to timeline
                new_timeline += new_segment
                # reinitialize current segment
                new_segment = segment
        # add last current segment to timeline
        new_timeline += new_segment
        
        return new_timeline
    
    def duration(self):
        """
        Return total duration of timeline coverage
        """
        return sum( [segment.duration for s, segment in enumerate(self.coverage())] )
    
    # ------------------------------------------------------------------- #
    
    def __getitem__(self, key):
        """
        self.__getitem__(key) <==> self[key]
        
        Return segment or list of segments depending on key
        Use the expression 'timeline[key]'
        
        
        key : int, slice or Segment
            If int, return keyth segment
            If slice, return list of segments
        """        
        return self.__segments[key]
        
        # if isinstance(key, int) or isinstance(key, slice):
        #     return self.__segments[key]
        # else:
        #     raise TypeError("timeline indices must be integers or slice of integers, not %s" % (type(key).__name__))
    
    def index(self, segment):
        """
        Return position of segment in timeline.
        
        segment : Segment
            Segment to look for.
        
        Raise ValueError if segment is not one of the timeline segments
        """
        if isinstance(segment, Segment):
            index = self.__searchsorted(segment, self.__segments)-1
            try:
                if self[index] == segment:
                    return index
                else:
                    raise ValueError()
            except Exception, e:
                raise ValueError("segment %s is not in timeline" % (segment))
        else:
            raise TypeError("timelines can only be searched for Segment, not %s" % (type(segment).__name__))
    
    # ------------------------------------------------------------------- #
    
    def __get_intersecting(self, key):
        """
        Get sorted list of segments with non-emtpy intersection with key segment
        """
        if not key:
            return []
        
        # any intersecting segment starts before key ends 
        # and ends after key starts

        dummy_end = Segment(key.end-SEGMENT_PRECISION, key.end-SEGMENT_PRECISION)
        index = self.__searchsorted(dummy_end, self.__segments)
        # every segment in __segments[:index] starts before key ends
        
        dummy_start = RevSegment(Segment(key.start+SEGMENT_PRECISION, key.start+SEGMENT_PRECISION))
        xedni = self.__searchsorted(dummy_start, self.__rsegments)
        # every segment in __rsegments[xedni:] ends after key starts
        
        both = set(self.__segments[:index]) & set(self.__rsegments[xedni:])
        return sorted([rsegment.copy() for rsegment in both])
    
    def __call__(self, requested, mode='intersection'):
        """
        # Create sub-timeline. Default mode is 'intersection'.
        # ... made of segments fully included in requested segment
        sub_timeline = tl(requested_segment, mode='strict')
    
        # ... made of segments with non-emtpy intersection with requested segment 
        sub_timeline = tl(requested_segment, mode='loose')
    
        # ... same as loose, except segments that are not fully included 
        #     in requested segment are trimmed to be fully included 
        sub_timeline = tl(requested_segment, mode='intersection')
    
        # ... made of segments fully included in requested timeline coverage
        #     i.e. tl(timeline, mode) == tl(timeline.coverage(), mode)  
        sub_timeline = tl(timeline, mode='strict')
    
        # ... made of segments with non-empty intersection with requested timeline coverage
        sub_timeline = tl(timeline, mode='loose')
    
        # ... same as loose, excepet segments that are not fully included
        #     in requested timeline coverage are trimmed to be fully included 
        sub_timeline = tl(timeline, mode='intersection')
        """
        
        if isinstance(requested, Segment):
            segment = requested     
            isegments = self.__get_intersecting(segment)
            if mode == 'strict':
                isegments = [isegment for isegment in isegments if isegment in segment]
            elif mode == 'intersection':
                isegments = [isegment & segment for isegment in isegments]
            elif mode == 'loose':
                pass
            else:
                raise ValueError('Unsupported mode (%s).' % mode)
            timeline = Timeline(segments=isegments, video=self.video)
        elif isinstance(requested, Timeline):
            timeline = Timeline(video=self.video)
            for segment in requested.coverage():
                timeline += self.__call__(segment, mode=mode)
        else:
            raise TypeError('')
        
        return timeline
    
    # =================================================================== #
    
    def __setitem__(self, key, value):
        raise NotImplementedError()
    
    # =================================================================== #
    
    def __delitem__(self, key):
        """
        Remove segments from timeline
        
        del timeline[i]
            Remove ith segment
        
        del timeline[i:j]
            Remove segments i to j-1
            
        del timeline[segment]
            Remove segment
            Raises an error if timeline does not contain segment.        
        """
        if isinstance(key, int):
            segment = self.__segments[key]
            yek = self.__searchsorted(RevSegment(segment), self.__rsegments)-1
            del self.__segments[key]
            del self.__rsegments[yek]
        elif isinstance(key, slice):
            segments = self.__segments[key]
            for s, segment in enumerate(segments):
                index = self.__searchsorted(segment, self.__segments)-1
                xedni = self.__searchsorted(RevSegment(segment), self.__rsegments)-1
                del self.__segments[index]
                del self.__rsegments[xedni]                
        elif isinstance(key, Segment):
            i = self.index(key)
            self.__delitem__(i)
        else:
            raise TypeError('')
    
    # ------------------------------------------------------------------- #
    
    def clear(self):
        """
        Remove all segments from this timeline.
        """
        del self.__segments[:]
        del self.__rsegments[:]
    
    # =================================================================== #
    
    def copy(self):
        """
        new_timeline = timeline.copy()
            create new timeline, identical to timeline
        """
        timeline = Timeline(video=self.video)
        timeline += self
        return timeline
    
    # =================================================================== #
    
    def __eq__(self, other):
        """
        Two timelines are identical if they contain the same segments.
        Use expression 'timeline1 == timeline2'
        """
        if isinstance(other, Timeline):
            return (len(self) == len(other)) and \
                    all([segment == other[s] for s, segment in enumerate(self)])
        else:
            return False

    def __ne__(self, other):
        """
        Use expression 'timeline1 != timeline2'
        """
        if isinstance(other, Timeline):
            return (len(self) != len(other)) or \
                    any([segment != other[s] for s, segment in enumerate(self)])
        else:
            return True
    
    # =================================================================== #
    
    def __str__(self):
        string = "[\n"
        for s, segment in enumerate(self):
            string += "   " + str(segment) + "\n"
        string += "]"
        return string
    
    # =================================================================== #

    def __ispartition(self):
        if not self:
            return True
        
        end = self[0].end
        for s, segment in enumerate(self[1:]):
            # use Segment.__nonzero__ (for precision-related reasons...)
            if Segment(start=segment.start, end=end):
                return False
            end = segment.end
        return True
    
    def __gt__(self, other):
        """
        Check whether timeline is a partition
        Use expression 'timeline > 0'
        """
        if other != 0:
            raise ValueError('Timeline can only be compared with 0 to test for partition.')
        return self.__ispartition()
    
    def __lt__(self, other):
        """
        Check whether timeline is not a partition
        Use expression 'timeline < 0'
        """
        return not self.__gt__(other)
    
    # ------------------------------------------------------------------
    
    def __abs__(self):
        """
        Partition timeline

        A picture is worth a thousand words.

        if timeline segments are like this:
        |------|    |------|     |----|
          |--|    |-----|     |----------|

        abs(timeline) segments are arranged like this:
        |-|--|-|  |-|---|--|  |--|----|--|
        """

        # if it is already a partition
        # return a copy
        if self > 0:
            return self.copy()

        new_timeline = Timeline(video=self.video)

        # get all boundaries (sorted)
        # |------|    |------|     |----|
        #   |--|    |-----|     |----------|
        # becomes
        # | |  | |  | |   |  |  |  |    |  |
        boundaries = []
        for s, segment in enumerate(self):
            start = segment.start
            end   = segment.end
            if start not in boundaries:
                boundaries.append(start)
            if end   not in boundaries:
                boundaries.append(end) 
        boundaries = sorted(boundaries)

        # create new partition timeline
        # | |  | |  | |   |  |  |  |    |  |
        # becomes
        # |-|--|-|  |-|---|--|  |--|----|--|
        start = boundaries[0]
        for b, boundary in enumerate(boundaries[1:]):
            new_segment = Segment(start=start, end=boundary)
            # do not add segments that are not included in the original timeline
            # if new_segment in self:
            if self.covers(new_segment, mode='strict'):
                new_timeline += Segment(start=start, end=boundary)
            start = boundary

        return new_timeline
    
    # =================================================================== #          
    def __contains__(self, other):
        
        # True if other segment is part of timeline
        # False otherwise
        if isinstance(other, Segment):
            try:
                i = self.index(other)
                return True
            except Exception, e:
                return False
        
        # True if all segment of other timeline is part of timeline
        # False otherwise
        elif isinstance(other, Timeline):
            return all([segment in self for segment in other])
        
        else:
            raise TypeError('')

    def covers(self, other, mode='strict'):
        """
        Check whether timeline covers other segment or timeline
        
        In 'strict' mode, return True if other segment (or all segments of
        other timeline) is contained by at least one segment of the timeline
        
        In 'loose' mode, uses timeline coverage instead of timeline
        
        """
        
        # in 'loose' mode, use timeline coverage in place of timeline
        if mode == 'loose':
            coverage = self.coverage()
            return coverage.covers(other, mode='strict')
        
        elif mode == 'strict':
            
            # True if other segment is contained 
            # by at least one segment of the timeline
            if isinstance(other, Segment):
                return any([other in segment \
                            for segment in self(other, mode='loose')])
            
            # True if timeline covers all other timeline segment
            elif isinstance(other, Timeline):
                return all([self.covers(segment, mode='strict') \
                            for segment in other])
                            
            else:
                raise TypeError('')
        else:
            raise ValueError('Unknown mode (strict or loose)')
        
    
    def __and__(self, other):
        raise NotImplementedError('')
        #return abs(self(other, mode='intersection'))
    
    def __or__(self, other):
        raise NotImplementedError('')
        # return abs(self + other)
    
    
    # ------------------------------------------------------------------
        
    def __invert__(self):
        """
        ~ timeline = 1 / timeline = timeline.extent() / timeline
        """
        return self.__rdiv__(self.extent())
    
    def __div__(self, other):
        return other.__rdiv__(self)
        
    def __rdiv__(self, other):
        """
        1 / timeline = timeline.extent() / timeline
        other_segment / timeline
        other_timeline / timeline 
        """
        
        # 1 / timeline == timeline.extent() / timeline
        if other == 1:
            itimeline = self.__rdiv__(self.extent())
        
        # other_timeline / timeline
        elif isinstance(other, Timeline):
            itimeline = Timeline(video=self.video)
            for segment in other.coverage():
                itimeline += (segment / self)
        
        # other_segment / timeline
        elif isinstance(other, Segment):
            itimeline = Timeline(video=self.video)
            end = other.start
            for segment in self(other, mode='intersection').coverage():
                itimeline += Segment(start=end, end=segment.start)
                end = segment.end
            itimeline += Segment(start=end, end=other.end)

        else:
            raise ValueError('')

        return itimeline
    