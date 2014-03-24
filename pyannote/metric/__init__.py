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

"""
Module :mod:`pyannote.metric` implements several evaluation metrics.

Most of them can be accumulated over multiple documents in order to obtain both
an aggregated error and confidence intervals. It is as easy as:

    >>> metric = MyMetric()
    >>> for reference, hypothesis in iterator:
    ...     local_value = metric(reference, hypothesis)
    >>> aggregated_value = abs(metric)
    >>> mean, (lower_bound, upper_bound) = metric.confidence_interval()

See :class:`pyannote.metric.base.BaseMetric` for details on how to contribute
your own metrics.

"""


__all__ = [
    'DetectionErrorRate',
    'DiarizationErrorRate',
    'IdentificationErrorRate',
    'f_measure'
]

from detection import DetectionErrorRate
from diarization import DiarizationErrorRate
from identification import IdentificationErrorRate
from segmentation import SegmentationPurity, SegmentationCoverage
from base import f_measure

if __name__ == "__main__":
    import doctest
    doctest.testmod()
