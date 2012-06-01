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

Clustering
==========

.. automodule:: pyannote.algorithm.clustering

Agglomerative clustering
************************

.. autoclass:: pyannote.algorithm.clustering.base.BaseAgglomerativeClustering
    :members:


Models
``````

.. automodule:: pyannote.algorithm.clustering.model

.. autoclass:: pyannote.algorithm.clustering.model.BICModelMixin
    :members:


Constraints
```````````

.. automodule:: pyannote.algorithm.clustering.constraint

.. autoclass:: pyannote.algorithm.clustering.constraint.ContiguousConstraintMixin
    :members:


Stopping criteria
`````````````````

.. automodule:: pyannote.algorithm.clustering.stop

.. autoclass:: pyannote.algorithm.clustering.stop.NegativeStoppingCriterionMixin
    :members:


