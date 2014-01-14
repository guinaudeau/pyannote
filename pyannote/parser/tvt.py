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

import pandas
from pyannote import LabelMatrix
from pyannote import Segment


# # convert head_XXX to XXX
# def _get_track(field):
#     return field.split('_')[1]


class TVTParser(object):
    """

    File format
    -----------
    uri start_time duration track_name other_track_name distance
    """

    def __init__(self):
        super(TVTParser, self).__init__()

    def read(self, path):

        # load text file at `path`
        # uri start_time duration track other_track distance
        names = ['u', 'start', 'duration', 't1', 't2', 'distance']
        # converters = {
        #     't1': _get_track,
        #     't2': _get_track
        # }
        converters = None
        table = pandas.read_table(
            path, sep='[\t ]+', header=None,
            names=names, converters=converters)

        # create pivot table with row `track, start_time, duration`,
        # column `other_track` and value `distance`
        pivot = pandas.pivot_table(
            table, values='distance',
            rows=['t1', 'start', 'duration'],
            cols=['t2'])

        # build dictionary to translate unique `track` name
        # to `segment, track` tuple
        T = {t: (Segment(start=s, end=s+d), t) for (t, s, d) in pivot.index}

        # get (segment, track) rows & columns ready
        rows = [T[_t] for (_t, _, _) in pivot.index]
        cols = [T[_t] for _t in pivot.columns]
        data = pivot.values

        # return (segment, track) similarity matrix
        return LabelMatrix(data=data, rows=rows, columns=cols)
