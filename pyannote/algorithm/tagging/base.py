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


from pyannote.base.timeline import Timeline
from pyannote.base.annotation import Annotation


class BaseTagger(object):
    """
    Base class for tagging algorithms.

    Parameters
    ----------
    annotation : bool, optional
        True if tagger supports ``Annotation`` tagging. Defaults to False
    timeline : bool, optional
        True if tagger supports ``Timeline`` tagging. Default to False.

    Returns
    -------
    tagger : BaseTagger

    """
    def __init__(self, annotation=False, timeline=False):
        super(BaseTagger, self).__init__()
        self.__taggable = set([])
        if annotation:
            self.__taggable.add(Annotation)
        if timeline:
            self.__taggable.add(Timeline)
        self.__taggable = tuple(self.__taggable)
    def __get_taggable(self):
        return self.__taggable
    taggable = property(fget=__get_taggable)
    """Taggable objects."""

    def _tag_timeline(self, source, timeline):
        """Must be implemented by inheriting ``Timeline`` tagger.

        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        timeline : Timeline
            Target timeline whose segments will be tagged.

        Returns
        -------
        tagged : Annotation
            Tagged `timeline`

        """
        raise NotImplementedError('._tag_timeline() is not implemented.')

    def _tag_annotation(self, source, annotation):
        """Must be implemented by inheriting ``Annotation`` tagger.

        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        annotation : Annotation
            Target annotation whose tracks will be tagged.

        Returns
        -------
        tagged : Annotation
            Tagged `annotation`

        """
        raise NotImplementedError('._tag_annotation() is not implemented.')

    def _check(self, source, target):
        """Check source and target format.

        Parameters
        ----------
        source, target : any object.

        Returns
        -------
        (source, target) if `source` and `target` are compatible with tagger.

        Raises
        ------
        TypeError if `source` is not an ``Annotation`` or ``target`` is not
        taggable by the tagger.
        ValueError if `source` and `target` resources are not the same.

        """

        # source must be Annotation
        if not isinstance(source, Annotation):
            raise TypeError("untaggable source type: '%s'. Must be "
                            "Annotation." % type(source).__name__)

        if not isinstance(target, self.__taggable):
            raise TypeError("untaggable target type: '%s'." \
                            % type(target).__name__,)

        # source and target resources must match
        if source.uri != target.uri:
            raise ValueError("source/target resource mismatch: '%s' and '%s'" \
                             % (source.uri, target.uri))

        return source, target

    def __call__(self, source, target):
        """Tag `target` based on `source` labels.

        Parameters
        ----------
        source : Annotation
            Source annotation whose labels will be propagated
        target : Timeline or Annotation
            Target timeline (or annotation) whose segment (or tracks) will be
            tagged

        Returns
        -------
        tagged: Annotation
            Tagged target.

        """
        source, target = self._check(source, target)
        if isinstance(target, Timeline):
            return self._tag_timeline(source, target)
        elif isinstance(target, Annotation):
            return self._tag_annotation(source, target)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
