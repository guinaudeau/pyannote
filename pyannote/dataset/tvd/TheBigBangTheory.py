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


from pyannote.dataset.tvd import TVD, Season


class TheBigBangTheory(TVD):

    SERIES = 'TheBigBangTheory'

    # Main characters
    MANUAL_MAIN_CHAR = [
        'leonard', 'sheldon', 'penny', 'howard', 'raj']

    # Other characters
    MANUAL_OTHR_CHAR = ['other']

    # Other labels
    MANUAL_OTHR_LBLS = [
        'laugh', 'sil', 'titlesong', 'ns', 'laughclap', 'mix']

    def __init__(self, tvd_dir=None):
        super(TheBigBangTheory, self).__init__(tvd_dir=tvd_dir)

    def get_season(self, season):
        return Season(self.__class__.__name__, season)

    def get_reference_speech_nonspeech(self, episode, language=None):

        kit = self.get_annotation(episode, 'KIT_sid_manual', 'mdtm')

        translation = {}
        for label in self.MANUAL_MAIN_CHAR + self.MANUAL_OTHR_CHAR:
            translation[label] = 'speech'
        for label in self.MANUAL_OTHR_LBLS:
            translation[label] = 'non_speech'

        return kit % translation

    def get_reference_speaker_identification(self, episode):

        kit = self.get_annotation(episode, 'KIT_sid_manual', 'mdtm')

        return kit.subset(set(self.MANUAL_MAIN_CHAR + self.MANUAL_OTHR_CHAR))
