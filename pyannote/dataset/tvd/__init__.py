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

import wave
import os.path
import contextlib
from collections import namedtuple
from pyannote import Segment, Timeline, Annotation
from pyannote.parser.annotation import AnnotationParser
from pyannote.parser.timeline import TimelineParser

DATASET = {

    'TheBigBangTheory': {
        'episodes': [17, 23, 23, 24, 24, 24],              # number of episodes
                                                           # per season
        'language': 'en'                                   # original language
    },

    'GameOfThrones': {
        'episodes': [5],
        'language': 'en'
    }

}


class Episode(namedtuple('Episode', ['series', 'season', 'episode'])):
    """
    Parameters
    ----------
    series : str
    season : int
    episode : int
    """

    def __new__(cls, series, season, episode):
        return super(Episode, cls).__new__(cls, series, season, episode)

    def __str__(self):
        return '%s.Season%02d.Episode%02d' % (
            self.series, self.season, self.episode)

    def __iter__(self):
        yield self


class Season(object):
    """
    Parameters
    ----------
    series : str
    season : int
    """
    def __init__(self, series, season):
        super(Season, self).__init__()
        self.series = series
        self.season = season
        self.episodes = [
            Episode(series, season, e+1)
            for e in range(DATASET[series]['episodes'][season-1])
        ]

    def __iter__(self):
        for episode in self.episodes:
            yield episode


class Series(object):
    """
    Parameters
    ----------
    series : str

    """
    def __init__(self, series):
        super(Series, self).__init__()
        self.series = series
        self.episodes = [
            Episode(series, s+1, e+1)
            for s in range(len(DATASET[series]['episodes']))
            for e in range(DATASET[series]['episodes'][s])
        ]

    def __iter__(self):
        for episode in self.episodes:
            yield episode


class TVD(object):

    """
    [TVD_ROOT]/[SERIES]/[TYPE]/[SERIES].Season[SEASON].Episode[EPISODE].[EXT]
    """

    def __init__(self, tvd_dir=None):

        super(TVD, self).__init__()
        if tvd_dir is None:
            tvd_dir = '.'
        self.tvd_dir = tvd_dir

    def get_annotation(self, episode, sub_dir, extension):

        series = episode.series
        uri = str(episode)
        filename = '%s.%s' % (uri, extension)

        path = os.path.join(self.tvd_dir, series, sub_dir, filename)
        annotation = AnnotationParser().read(path, uri=uri)(uri=uri)

        return annotation

    def get_timeline(self, episode, sub_dir, extension):

        series = episode.series
        uri = str(episode)
        filename = '%s.%s' % (uri, extension)

        path = os.path.join(self.tvd_dir, series, sub_dir, filename)
        timeline = TimelineParser().read(path, uri=uri)(uri=uri)

        return timeline

    def get_wav(self, episode, language=None):
        """Get path to .wav file

        Parameters
        ----------
        episode : Episode
        language : str, optional
            Defaults to series original language.

        Returns
        -------
        path : str
            Path to .wav file
        """

        series = episode.series
        if language is None:
            language = DATASET[series]['language']
        filename = '%s.%s.wav' % (str(episode), language)

        return os.path.join(self.tvd_dir, series, 'wav', filename)

    def get_episode_extent_from_wav(self, episode):
        """Get episode duration from .wav file

        Parameters
        ----------
        episode : Episode

        Returns
        -------
        extent : Segment
            Episode extent [0, duration] in seconds.
        """
        wav = self.get_wav(episode)

        with contextlib.closing(wave.open(wav, 'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            extent = Segment(start=0, end=frames/float(rate))

        return extent

    def get_features_from_wav(self, featureExtractor, episode, language=None):
        """Apply feature extraction on .wav file

        Parameters
        ----------
        featureExtractor :
        episode : Episode
        language : str, optional
            Defaults to series original language.
        """
        wav = self.get_wav(episode, language=language)
        return featureExtractor.extract(wav)

    def get_subtitles_speech_nonspeech(self, episode, language=None):
        """"""

        series = episode.series

        if language is None:
            language = DATASET[series]['language']

        subtitles = self.get_timeline(episode, 'DVD_sub', '%s.srt' % language)
        extent = self.get_episode_extent_from_wav(episode)

        speech = subtitles.coverage()
        non_speech = subtitles.gaps(focus=extent)

        a = Annotation(uri=str(episode), modality='speech activity detection')
        for s in speech:
            a[s, '_'] = 'speech'
        for s in non_speech:
            a[s, '_'] = 'non_speech'

        return a
