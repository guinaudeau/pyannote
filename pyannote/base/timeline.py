#!/usr/bin/env python
# encoding: utf-8

# Copyright 2012-2013 Herve BREDIN (bredin@limsi.fr)

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
from banyan import SortedSet


class TimelineUpdator(object):

    class Metadata(object):

        def update(self, key, key_fn, left, right):

            # number of segments in tree
            self.num = 1
            if left:
                self.num += left.num
            if right:
                self.num += right.num

            # minimum timestamp in tree
            self.min = key.start
            if left:
                self.min = min(self.min, left.min)

            # maximum timestamp in tree
            self.max = key.end
            if right:
                self.max = max(self.max, right.max)

        def __repr__(self):
            return 'MIN: %g | MAX %g | NUM %d' % (self.min, self.max, self.num)


class Timeline(object):
    """
    Ordered set of segments.

    A timeline can be seen as an ordered set of non-empty segments (Segment).
    Segments can overlap -- though adding an already exisiting segment to a
    timeline does nothing.

    Parameters
    ----------
    segments : Segment iterator, optional
        initial set of segments
    uri : string, optional
        name of segmented resource

    Returns
    -------
    timeline : Timeline
        New timeline

    Examples
    --------
    Create a new empty timeline

        >>> timeline = Timeline()
        >>> if not timeline:
        ...    print "Timeline is empty."
        Timeline is empty.

    Add one segment (+=)

        >>> segment = Segment(0, 1)
        >>> timeline.add(segment)
        >>> if len(timeline) == 1:
        ...    print "Timeline contains only one segment."
        Timeline contains only one segment.

    Add all segments from another timeline

        >>> other_timeline = Timeline([Segment(0.5, 3), Segment(6, 8)])
        >>> timeline.update(other_timeline)

    Get timeline extent, coverage & duration

        >>> extent = timeline.extent()
        >>> print extent
        [0 --> 8]
        >>> coverage = timeline.coverage()
        >>> print coverage
        [
           [0 --> 3]
           [6 --> 8]
        ]
        >>> duration = timeline.duration()
        >>> print "Timeline covers a total of %g seconds." % duration
        Timeline covers a total of 5 seconds.

    Iterate over (sorted) timeline segments

        >>> for segment in timeline:
        ...    print segment
        [0 --> 1]
        [0.5 --> 3]
        [6 --> 8]

    Segmentation

        >>> segmentation = timeline.segmentation()
        >>> print segmentation
        [
           [0 --> 0.5]
           [0.5 --> 1]
           [1 --> 3]
           [6 --> 8]
        ]

    Gaps

        >>> timeline = timeline.copy()
        >>> print timeline
        [
           [0 --> 1]
           [0.5 --> 3]
           [6 --> 8]
        ]
        >>> print timeline.gaps()
        [
           [3 --> 6]
        ]
        >>> segment = Segment(0, 10)
        >>> print timeline.gaps(segment)
        [
           [3 --> 6]
           [8 --> 10]
        ]

    """

    def __init__(self, segments=None, uri=None):
        super(Timeline, self).__init__()

        # sorted set of segments (as an augmented red-black tree)
        segments = [s for s in segments if s] if segments else []
        self._segments = SortedSet(items=segments,
                                   key_type=(float, float),
                                   updator=TimelineUpdator)

        # path to (or any identifier of) segmented resource
        self.uri = uri

    def __len__(self):
        root = self._segments.root
        if root:
            return root.metadata.num
        else:
            return 0

    def __iter__(self):
        return iter(self._segments)

    def __nonzero__(self):
        return len(self) > 0

    def add(self, segment):
        """Add segment"""
        if segment:
            self._segments.add(segment)

    def update(self, timeline):
        """Add `timeline` segments"""
        if self.uri == timeline.uri:
            self._segments.update(timeline._segments)
        else:
            raise ValueError('URI mismatch (%s vs. %s)' % (self.uri,
                                                           timeline.uri))

    def union(self, other):
        """Create new timeline made of union of segments"""
        if self.uri == other.uri:
            segments = self._segments.union(other._segments)
            return Timeline(segments=segments, uri=self.uri)

    def __tree(self, node, depth, metadata):
        if node:
            self.__tree(node.right, depth+2, metadata)
            if metadata:
                print " " * depth + str(node.key) + " " + str(node.metadata)
            else:
                print " " * depth + str(node.key)
            self.__tree(node.left, depth+2, metadata)

    def tree(self, metadata=False):
        """Print red-black tree used to store segments"""
        self.__tree(self._segments.root, 0, metadata)

    def __kth(self, node, k):
        """"""

        if node.left:

            # if there are exactly k elements in left child
            # then the kth (0-indexed) element is in root node
            if k == node.left.metadata.num:
                return node.key

            # if there are more than k elements in left child
            # then the kth element should be found in left child
            elif k < node.left.metadata.num:
                return self.__kth(node.left, k)

            # if there are less than k elements in left child
            # then the kth element should be found in right child
            else:
                return self.__kth(node.right, k-1-node.left.metadata.num)
        else:

            if k == 0:
                return node.key

            else:
                return self.__kth(node.right, k-1)

    def kth(self, k):
        """Get kth segment"""
        if 0 <= k and k < self._segments.root.metadata.num:
            return self.__kth(self._segments.root, k)
        else:
            raise IndexError('')

    def __order(self, node, segment, k):

        if node is None:
            raise ValueError('Timeline does not contain segment.')

        elif segment == node.key:
            return k + (node.left.metadata.num if node.left else 0)

        elif segment < node.key:
            return self.__order(node.left, segment, k)

        else:
            return self.__order(node.right, segment,
                                k+1+(node.left.metadata.num if node.left
                                     else 0))

    def order(self, segment):
        return self.__order(self._segments.root, segment, 0)

    def __dfs(self, node):
        """Depth-first search key iterator"""
        if node:
            for key in self.__dfs(node.left):
                yield key
            yield node.key
            for key in self.__dfs(node.right):
                yield key

    def __crop_loose(self, node, segment):
        """Returns segments overlapping query segment.
        """

        # empty list of segments
        segments = []

        # search left child if it exists
        if node.left:

            # if left child extent may intersect query `segment`
            # look for intersecting segments in left child
            left_extent = Segment(node.left.metadata.min, node.left.metadata.max)
            if left_extent.intersects(segment):

                # if left child extent is fully included in query `segment`
                # then every segment intersects query `segment`
                if left_extent in segment:
                    segments.extend([key for key in self.__dfs(node.left)])

                # otherwise, only some of them intersects it
                # and we must look for them
                else:
                    segments.extend(self.__crop_loose(node.left, segment))

        # add root segment if it intersects query `segment`
        if node.key.intersects(segment):
            segments.append(node.key)

        # search right child if it exists
        if node.right:

            # if right child extent may intersect query `segment`
            # look for intersecting segments in right child
            right_extent = Segment(node.right.metadata.min, node.right.metadata.max)
            if right_extent.intersects(segment):

                # if right child extent is fully included in query `segment`
                # then every segment intersects query `segment`
                if right_extent in segment:
                    segments.extend([key for key in self.__dfs(node.right)])

                # otherwise, only some of them intersects it
                # and we must look for them
                else:
                    segments.extend(self.__crop_loose(node.right, segment))

        # segments are naturally ordered (depth-first search)
        return segments

    def __crop_strict(self, node, segment):
        """Returns segments fully included in query `segment`.
        """

        # empty list of segments
        segments = []

        # search left child if it exists
        if node.left:

            # if left child extent may intersect query `segment`
            # look for intersecting segments in left child
            left_extent = Segment(node.left.metadata.min, node.left.metadata.max)
            if left_extent.intersects(segment):

                # if left child extent is fully included in query `segment`
                # then every segment intersects query `segment`
                if left_extent in segment:
                    segments.extend([key for key in self.__dfs(node.left)])

                # otherwise, only some of them intersects it
                # and we must look for them
                else:
                    segments.extend(self.__crop_strict(node.left, segment))

        # add root segment if it is fully included in query `segment`
        if node.key in segment:
            segments.append(node.key)

        # search right child if it exists
        if node.right:

            # if right child extent may intersect query `segment`
            # look for intersecting segments in right child
            right_extent = Segment(node.right.metadata.min, node.right.metadata.max)
            if right_extent.intersects(segment):

                # if right child extent is fully included in query `segment`
                # then every segment intersects query `segment`
                if right_extent in segment:
                    segments.extend([key for key in self.__dfs(node.right)])

                # otherwise, only some of them intersects it
                # and we must look for them
                else:
                    segments.extend(self.__crop_strict(node.right, segment))

        # segments are naturally ordered (depth-first search)
        return segments

    def __crop_inter(self, node, segment):
        """
        """

        # empty list of segments
        segments = []

        # search left child if it exists
        if node.left:

            # if left child extent may intersect query `segment`
            # look for intersecting segments in left child
            left_extent = Segment(node.left.metadata.min, node.left.metadata.max)
            if left_extent.intersects(segment):

                # if left child extent is fully included in query `segment`
                # then every segment intersects query `segment`
                if left_extent in segment:
                    segments.extend([(key, key) for key in self.__dfs(node.left)])

                # otherwise, only some of them intersects it
                # and we must look for them
                else:
                    segments.extend(self.__crop_inter(node.left, segment))

        # add root segment if it intersects query `segment`
        # (along with their actual intersection)
        if node.key.intersects(segment):
            segments.append((node.key, node.key & segment))

        # search right child if it exists
        if node.right:

            # if right child extent may intersect query `segment`
            # look for intersecting segments in right child
            right_extent = Segment(node.right.metadata.min, node.right.metadata.max)
            if right_extent.intersects(segment):

                # if right child extent is fully included in query `segment`
                # then every segment intersects query `segment`
                if right_extent in segment:
                    segments.extend([(key, key) for key in self.__dfs(node.right)])

                # otherwise, only some of them intersects it
                # and we must look for them
                else:
                    segments.extend(self.__crop_inter(node.right, segment))

        # segments are naturally ordered (depth-first search)
        return segments

    def crop(self, extent, mode='intersection', mapping=False):

        if isinstance(extent, Segment):

            # loose mode ==> use __crop_loose helper function
            if mode == 'loose':
                segments = self.__crop_loose(self._segments.root, extent)
                return Timeline(segments=segments, uri=self.uri)

            # strict mode ==> use __crop_strict helper function
            elif mode == 'strict':
                segments = self.__crop_strict(self._segments.root, extent)
                return Timeline(segments=segments, uri=self.uri)

            # intersection mode ==> use __crop_inter helper function
            elif mode == 'intersection':

                inter = self.__crop_inter(self._segments.root, extent)
                i2o = {}
                for original, intersection in inter:
                    i2o[intersection] = i2o.get(intersection, list()) + [original]
                if mapping:
                    return Timeline(i2o, uri=self.uri), i2o
                else:
                    return Timeline(i2o, uri=self.uri)

            else:
                raise NotImplementedError()

        elif isinstance(extent, Timeline):

            coverage = extent.coverage()

            if mode == 'loose':
                segments = []
                for segment in coverage:
                    segments.extend(self.__crop_loose(self._segments.root,
                                                      segment))
                return Timeline(segments=segments, uri=self.uri)

            elif mode == 'strict':
                segments = []
                for segment in coverage:
                    segments.extend(self.__crop_strict(self._segments.root,
                                                       segment))
                return Timeline(segments=segments, uri=self.uri)

            elif mode == 'intersection':
                i2o = {}
                for segment in coverage:
                    inter = self.__crop_inter(self._segments.root, segment)
                    for o, i in inter:
                        i2o[i] = i2o.get(i, list()) + [o]
                if mapping:
                    return Timeline(i2o, uri=self.uri), i2o
                else:
                    return Timeline(i2o, uri=self.uri)

            else:
                raise NotImplementedError()

    def __overlapping(self, node, t):

        segments = []

        if node.left and node.left.metadata.min <= t and node.left.metadata.max >= t:
            segments.extend(self.__overlapping(node.left, t))

        if node.key.start <= t and node.key.end >= t:
            segments.append(node.key)

        if node.right and node.right.metadata.min <= t and node.right.metadata.max >= t:
            segments.extend(self.__overlapping(node.right, t))

        return segments

    def overlapping(self, timestamp):
        """Get list of segments overlapping `timestamp`"""
        return self.__overlapping(self._segments.root, timestamp)

    def __eq__(self, other):
        return self.uri == other.uri and self._segments == other._segments

    def __ne__(self, other):
        return self.uri != other.uri or self._segments != other._segments

    def __str__(self):
        """Human-friendly representation"""

        string = "[\n"
        for segment in self._segments:
            string += "   %s\n" % str(segment)
        string += "]"
        return string

    def __repr__(self):
        return "<Timeline(%s)>" % list(self._segments)

    def __contains__(self, included):
        """Inclusion

        Use expression 'segment in timeline' or 'other_timeline in timeline'

        Parameters
        ----------
        included : Segment or Timeline

        Returns
        -------
        contains : bool
            True if every segment in `included` exists in timeline,
            False otherwise

        """

        if isinstance(included, Segment):
            return included in self._segments

        elif isinstance(included, Timeline):
            return self._segments.issuperset(included._segments)

        else:
            raise TypeError()

    def empty(self):
        """Empty copy of a timeline.

        Examples
        --------

            >>> timeline = Timeline(uri="MyVideo.avi")
            >>> timeline += [Segment(0, 1), Segment(2, 3)]
            >>> empty = timeline.empty()
            >>> print empty.uri
            MyVideo.avi
            >>> print empty
            [
            ]

        """
        return Timeline(uri=self.uri)

    def copy(self, segment_func=None):
        """Duplicate timeline.

        If segment_func is provided, apply it to each segment first.

        Parameters
        ----------
        segment_func : function

        Returns
        -------
        timeline : Timeline
            A (possibly modified) copy of the timeline

        Examples
        --------

            >>> timeline = Timeline(uri="MyVideo.avi")
            >>> timeline += [Segment(0, 1), Segment(2, 3)]
            >>> cp = timeline.copy()
            >>> print cp.uri
            MyVideo.avi
            >>> print cp
            [
               [0 --> 1]
               [2 --> 3]
            ]

        """

        # if segment_func is not provided
        # just add every segment
        if segment_func is None:
            return Timeline(segments=self._segments, uri=self.uri)

        # if is provided
        # apply it to each segment before adding them
        else:
            return Timeline(segments=[segment_func(s) for s in self._segments],
                            uri=self.uri)

    def extent(self):
        """Timeline extent

        The extent of a timeline is the segment of minimum duration that
        contains every segments of the timeline. It is unique, by definition.
        The extent of an empty timeline is an empty segment.

        Returns
        -------
        extent : Segment
            Timeline extent

        Examples
        --------

            >>> timeline = Timeline(uri="MyVideo.avi")
            >>> timeline += [Segment(0, 1), Segment(9, 10)]
            >>> print timeline.extent()
            [0 --> 10]

        """
        return Segment() if self._segments.root is None \
            else Segment(self._segments.root.metadata.min,
                         self._segments.root.metadata.max)

    def coverage(self):
        """Timeline coverage

        The coverage of timeline is the timeline with the minimum number of
        segments with exactly the same time span as the original timeline.
        It is (by definition) unique and does not contain any overlapping
        segments.

        Returns
        -------
        coverage : Timeline
            Timeline coverage

        """

        # make sure URI attribute is kept.
        coverage = Timeline(uri=self.uri)

        # The coverage of an empty timeline is an empty timeline.
        if not self:
            return coverage

        # Principle:
        #   * gather all segments with no gap between them
        #   * add one segment per resulting group (their union |)
        # Note:
        #   Since segments are kept sorted internally,
        #   there is no need to perform an exhaustive segment clustering.
        #   We just have to consider them in their natural order.

        # Initialize new coverage segment
        # as very first segment of the timeline
        new_segment = self.kth(0)

        for segment in self:

            # If there is no gap between new coverage segment and next segment,
            if not (segment ^ new_segment):
                # Extend new coverage segment using next segment
                new_segment |= segment

            # If there actually is a gap,
            else:
                # Add new segment to the timeline coverage
                coverage.add(new_segment)
                # Initialize new coverage segment as next segment
                # (right after the gap)
                new_segment = segment

        # Add new segment to the timeline coverage
        coverage.add(new_segment)

        return coverage

    def duration(self):
        """Timeline duration

        Returns
        -------
        duration : float
            Duration of timeline coverage, in seconds.

        """

        # The timeline duration is the sum of the durations
        # of the segments in the timeline coverage.
        return sum([s.duration for s in self.coverage()])

    # def gaps(self, focus=None):
    #     """Timeline gaps

    #     Parameters
    #     ----------
    #     focus : None, Segment or Timeline

    #     Returns
    #     -------
    #     gaps : Timeline
    #         Timeline made of all gaps from original timeline, and delimited
    #         by provided segment or timeline.

    #     Raises
    #     ------
    #     TypeError when `focus` is neither None, Segment nor Timeline

    #     Examples
    #     --------

    #     """
    #     if focus is None:
    #         focus = self.extent()

    #     if not isinstance(focus, (Segment, Timeline)):
    #         raise TypeError("unsupported operand type(s) for -':"
    #                         "%s and Timeline." % type(focus).__name__)

    #     # segment focus
    #     if isinstance(focus, Segment):

    #         # starts with an empty timeline
    #         timeline = self.empty()

    #         # `end` is meant to store the end time of former segment
    #         # initialize it with beginning of provided segment `focus`
    #         end = focus.start

    #         # focus on the intersection of timeline and provided segment
    #         for segment in self.crop(focus, mode='intersection').coverage():

    #             # add gap between each pair of consecutive segments
    #             # if there is no gap, segment is empty, therefore not added
    #             # see .__iadd__ for more information.
    #             timeline += Segment(start=end, end=segment.start)

    #             # keep track of the end of former segment
    #             end = segment.end

    #         # add final gap (if not empty)
    #         timeline += Segment(start=end, end=focus.end)

    #     # other_timeline - timeline
    #     elif isinstance(focus, Timeline):

    #         # starts with an empty timeline
    #         timeline = self.empty()

    #         # add gaps for every segment in coverage of provided timeline
    #         for segment in focus.coverage():
    #             timeline += self.gaps(focus=segment)

    #     return timeline

    def segmentation(self):
        """Non-overlapping timeline

        Create the unique timeline with same coverage and same set of segment
        boundaries as original timeline, but with no overlapping segments.

        A picture is worth a thousand words:

            Original timeline:
            |------|    |------|     |----|
              |--|    |-----|     |----------|

            Non-overlapping timeline
            |-|--|-|  |-|---|--|  |--|----|--|

        Returns
        -------
        timeline : Timeline

        Examples
        --------

            >>> timeline = Timeline()
            >>> timeline += [Segment(0, 1), Segment(1, 2), Segment(2,3)]
            >>> timeline += [Segment(2, 4), Segment(6, 7)]
            >>> print timeline.segmentation()
            [
               [0 --> 1]
               [1 --> 2]
               [2 --> 3]
               [3 --> 4]
               [6 --> 7]
            ]

        """
        # COMPLEXITY: O(n)
        coverage = self.coverage()

        # COMPLEXITY: O(n.log n)
        # get all boundaries (sorted)
        # |------|    |------|     |----|
        #   |--|    |-----|     |----------|
        # becomes
        # | |  | |  | |   |  |  |  |    |  |
        timestamps = set([])
        for (start, end) in self:
            timestamps.add(start)
            timestamps.add(end)
        timestamps = sorted(timestamps)

        # create new partition timeline
        # | |  | |  | |   |  |  |  |    |  |
        # becomes
        # |-|--|-|  |-|---|--|  |--|----|--|

        # start with an empty copy
        timeline = Timeline(uri=self.uri)
        segments = []

        start = timestamps[0]
        for end in timestamps[1:]:
            # only add segments that are covered by original timeline
            segment = Segment(start=start, end=end)
            if segment and coverage.overlapping(segment.middle):
                segments.append(segment)
            start = end

        timeline._segments.update(segments)

        return timeline

    def to_json(self):
        return [s.to_json() for s in self]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
