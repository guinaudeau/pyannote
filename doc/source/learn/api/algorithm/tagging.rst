.. This file is part of PyAnnote

      PyAnnote is free software: you can redistribute it and/or modify
      it under the terms of the GNU General Public License as published by
      the Free Software Foundation, either version 3 of the License, or
      (at your option) any later version.
  
      PyAnnote is distributed in the hope that it will be useful,
      but WITHOUT ANY WARRANTY; without even the implied warranty of
      MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
      GNU General Public License for more details.
  
      You should have received a copy of the GNU General Public License
      along with PyAnnote.  If not, see <http://www.gnu.org/licenses/>.

Tagging
=======

.. automodule:: pyannote.algorithm.tagging

Base type
*********

.. autoclass:: pyannote.algorithm.tagging.base.BaseTagger
    :members: _tag_timeline, _tag_annotation, __call__

Label tagging
**************

.. automodule:: pyannote.algorithm.tagging.label

.. autoclass:: pyannote.algorithm.tagging.label.LabelTagger
    :members: __call__

.. autoclass:: pyannote.algorithm.tagging.label.HungarianTagger
    :members: __call__
    :show-inheritance:

.. autoclass:: pyannote.algorithm.tagging.label.ArgMaxTagger
    :members: __call__
    :show-inheritance:

Segment tagging
***************

.. automodule:: pyannote.algorithm.tagging.segment

.. autoclass:: pyannote.algorithm.tagging.segment.ConservativeDirectTagger
    :members:
    :undoc-members:

.. autoclass:: pyannote.algorithm.tagging.segment.ArgMaxDirectTagger
    :members:
    :undoc-members:

