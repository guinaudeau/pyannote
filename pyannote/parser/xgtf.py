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
XGTF () is a file format used by ViPER video annotation tool.

References
----------
http://viper-toolkit.sourceforge.net/
"""

import re
from lxml import objectify
from pyannote.base.segment import Segment
from base import BaseAnnotationParser
from idx import IDXParser


class XGTFParser(BaseAnnotationParser):

    def __init__(self):
        super(XGTFParser, self).__init__()
        self.__idx = IDXParser()

    def _parse_frame(self, element):

        string = element.get('framespan')
        if not string:
            return Segment()

        p = re.compile('([0-9]*):([0-9]*)')
        m = p.match(string)
        return self.__idx[int(m.group(1))]

    def _parse_head(self, vpr):
        return [vpr.getchildren()[0].get('value')]

    def _parse_time(self, vpr):
        return self.__idx(int(vpr.getchildren()[0].get('value')))

    def _parse_cartouche(self, vpr):
        children = vpr.getchildren()
        if children:
            return vpr.getchildren()[0].get('value')
        else:
            return False

    def _parse_written(self, vpr, alone=False):
        """

        Parameters
        ----------
        alone : bool
            If True, only keep written names that are alone on their text line
            If False (default), keep them all
        """
        string = vpr.getchildren()[0].get('value')
        if not string:
            return []

        labels = []
        if alone:
            #         group  #1         #2         #3     #4
            p = re.compile('(.*?)<pers=(.*?)>.*?(</pers>)(.*)', re.DOTALL)
            m = p.match(string)
            while(m):
                beforeOnSameLine = m.group(1).split('\\n')[-1].strip()
                afterOnSameLine = m.group(4).split('\\n')[0].strip()
                if beforeOnSameLine == '' and afterOnSameLine == '':
                    labels.append(str(m.group(2)))
                string = string[m.end(3):]
                m = p.match(string)
        else:
            p = re.compile('.*?<pers=(.*?)>.*?</pers>', re.DOTALL)
            m = p.match(string)
            while(m):
                labels.append(str(m.group(1)))
                string = string[m.end():]
                m = p.match(string)

        return labels

    def read(self, path_xgtf, path_idx=None, uri=None):

        # frame <--> timestamp mapping
        self.__idx.read(path_idx)

        # objectify xml file and get root
        root = objectify.parse(path_xgtf).getroot().data.sourcefile

        if uri is None:
            uri = root.get('filename')

        head = []
        written = []
        written_alone = []

        for element in root.iterchildren():

            frame_segment = self._parse_frame(element)
            if frame_segment and frame_segment not in self(uri, "annotated"):
                self._add(frame_segment, "_", "_", uri, "annotated")

            if element.get('name') in ['PERSONNE', 'TEXTE']:

                written = set([])
                written_alone = set([])
                written_intro = set([])
                head = set([])
                cartouche = False

                for vpr in element.iterchildren():

                    attr_name = vpr.get('name')
                    if attr_name == 'STARTFRAME':
                        element_start = self._parse_time(vpr)
                    elif attr_name == 'ENDFRAME':
                        element_end = self._parse_time(vpr)
                    elif attr_name == 'TRANSCRIPTION':
                        written_alone = self._parse_written(vpr, alone=True)
                        written = self._parse_written(vpr, alone=False)
                    elif attr_name == 'NOM':
                        head = self._parse_head(vpr)
                    elif attr_name == 'CARTOUCHE':
                        cartouche = self._parse_cartouche(vpr)

                if cartouche:
                    written_intro = set(written)

                element_segment = Segment(start=element_start, end=element_end)

                try:
                    modalities = {
                        'written (alone)': written_alone,
                        'written (intro)': written_intro,
                        'written': written,
                        'head': head}

                    for modality, new_lbls in modalities.iteritems():

                        for lbl in new_lbls:
                            lbls = self(uri,
                                        modality).get_labels(element_segment)
                            if lbl not in lbls:
                                self._add(element_segment, None, lbl,
                                          uri, modality)
                except Exception, e:
                    print "Error @ %s %f %f" % (uri, element_start,
                                                element_end)
                    raise e

        return self

    def _get_transcription(self, vpr):
        string = vpr.getchildren()[0].get('value')
        if not string:
            return ""
        return string

    def print_raw_text(self, path_xgtf):

        string = ""
        # objectify xml file and get root
        root = objectify.parse(path_xgtf).getroot().data.sourcefile

        for element in root.iterchildren():

            if element.get('name') == 'TEXTE':

                transcription = ""
                cartouche = False

                for vpr in element.iterchildren():

                    attr_name = vpr.get('name')
                    if attr_name == 'TRANSCRIPTION':
                        transcription = self._get_transcription(vpr)
                    elif attr_name == 'CARTOUCHE':
                        cartouche = self._parse_cartouche(vpr)

                if transcription == "":
                    continue

                string += "%d %s\n" % (bool(cartouche),
                                       unicode(transcription).encode('UTF-8'))
        return string

if __name__ == "__main__":
    import doctest
    doctest.testmod()
