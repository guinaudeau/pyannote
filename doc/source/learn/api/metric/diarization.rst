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

Diarization
===========

.. automodule:: pyannote.metric.diarization

.. autosummary::
   :nosignatures:
   
   pyannote.metric.diarization.DiarizationErrorRate
   pyannote.metric.diarization.DiarizationCoverage
   pyannote.metric.diarization.DiarizationPurity
   pyannote.metric.diarization.DiarizationHomogeneity
   pyannote.metric.diarization.DiarizationCompleteness

.. autoclass:: pyannote.metric.diarization.DiarizationErrorRate
    :members: name, __call__, __abs__, __iter__, __getitem__, confidence_interval, reset, optimal_mapping

.. autoclass:: pyannote.metric.diarization.DiarizationCoverage
    :members:
    :inherited-members:
    :special-members:

.. autoclass:: pyannote.metric.diarization.DiarizationPurity
    :members:
    :inherited-members:
    :special-members:

.. autoclass:: pyannote.metric.diarization.DiarizationHomogeneity
    :members:
    :inherited-members:
    :special-members:

.. autoclass:: pyannote.metric.diarization.DiarizationCompleteness
    :members:
    :inherited-members:
    :special-members:
