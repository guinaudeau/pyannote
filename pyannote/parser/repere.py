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
REPERE file format

References
----------
http://www.defi-repere.fr
"""

from pyannote.base.segment import Segment
from pyannote.base import URI, MODALITY, LABEL, SCORE
from base import \
    BaseTextualAnnotationParser, \
    BaseTextualScoresParser, \
    BaseTextualFormat


def get_show_name(uri):
    """

    Parameters
    ----------
    uri : str
        Uniform Resource Identifier

    Returns
    -------
    show : str
        Name of the show

    Examples
    --------

        >>> print get_show_name('BFMTV_PlaneteShowbiz_20110705_195500')
        BFMTV_PlaneteShowbiz

    """
    tokens = uri.split('_')
    channel = tokens[0]
    show = tokens[1]
    return channel + '_' + show


def is_unknown(identifier):
    """

    Parameters
    ----------
    identifier : str
        Person identifier

    Returns
    -------
    unknown : bool
        True if `identifier` is unknow ('Inconnu_XXX' or 'speakerXXX')

    """
    return identifier[:8] == 'Inconnu_' or identifier[:7] == 'speaker'


class REPEREMixin(BaseTextualFormat):

    START = 'start'
    END = 'end'

    def get_comment(self):
        return ';'

    def get_separator(self):
        return '[ \t]+'

    def get_fields(self):
        return [URI,
                self.START,
                self.END,
                MODALITY,
                LABEL]

    def get_segment(self, row):
        return Segment(row[self.START], row[self.END])

    def _append(self, annotation, f, uri, modality):
        try:
            format = '%s %%g %%g %s %%s\n' % (uri, modality)
            for segment, track, label in annotation.iterlabels():
                f.write(format % (segment.start, segment.end, label))
        except Exception, e:
            print "Error @ %s%s %s %s" % (uri, segment, track, label)
            raise e


class REPEREParser(BaseTextualAnnotationParser, REPEREMixin):
    pass


class REPEREScoreMixin(BaseTextualFormat):

    START = 'start'
    END = 'end'

    def get_comment(self):
        return ';'

    def get_separator(self):
        return '[ \t]+'

    def get_fields(self):
        return [URI,
                self.START,
                self.END,
                MODALITY,
                LABEL,
                SCORE]

    def get_segment(self, row):
        return Segment(row[self.START], row[self.END])

    def _append(self, scores, f, uri, modality):
        try:
            format = '%s %%g %%g %s %%s %%g\n' % (uri, modality)
            for segment, track, label, value in scores.itervalues():
                f.write(format % (segment.start, segment.end,
                                  label, value))
        except Exception, e:
            print "Error @ %s%s %s %s" % (uri, segment, track, label)
            raise e


class REPEREScoresParser(BaseTextualScoresParser, REPEREScoreMixin):
    pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
