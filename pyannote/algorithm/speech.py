#!/usr/bin/env python
# encoding: utf-8

# Copyright 2013 Herve BREDIN (bredin@limsi.fr)

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


import sys
import pickle
import datetime
import itertools
from pyannote.algorithm.segmentation import \
    SegmentationHMM, SegmentationGaussianDivergence


class SpeechActivityDetection(object):
    """Speech activity detection based on 2-states HMM

    Generate a speech/non-speech annotation from a .wav file

    Example
    -------

    >>> hmm = SegmentationHMM(n_components=16, covariance_type='diag')
    >>> sad = SpeechActivityDetection(hmm)
    >>> reference = [...]
    >>> wav = [...]
    >>> sad.fit(reference, wav=wav)
    >>> new_wav = '...'
    >>> annotation = sad.apply(new_wav)

    Parameters
    ----------
    hmm : SegmentationHMM
        HMM (pre-trained or not)
    min_duration, float, optional
        Set minimum duration of speech/non-speech segments to `min_duration`
        (in seconds). Defaults to 250ms.
    feature : optional
        Defaults to MFCC with 12 coefficients, their delta, and delta energy.
    cache : bool, optional
        Whether to cache feature extraction (True) or not (False).
        Defaults to False.
    """

    SPEECH = 'speech'
    NON_SPEECH = 'non_speech'

    def __init__(
        self,
        hmm=None,
        n_components=16, covariance_type='diag',
        min_duration=0.250,
        feature=None, cache=False
    ):

        super(SpeechActivityDetection, self).__init__()

        self.hmm = hmm
        self.hmm.min_duration = min_duration

        # default features for speech activity detection
        # are MFCC (12 coefficients + delta coefficient + delta energy)
        if feature is None:
            from pyannote.feature.yaafe import YaafeMFCC
            feature = YaafeMFCC(e=False, coefs=12, De=True, D=True)
        self.feature = feature

        if cache:

            # initialize cache
            from joblib import Memory
            from tempfile import mkdtemp
            memory = Memory(cachedir=mkdtemp(), verbose=0)

            # cache feature extraction method
            self.get_features = memory.cache(self.get_features)

    def get_features(self, wav):
        return self.feature.extract(wav)

    def fit(self, reference, wav=None, features=None):
        """
        reference : iterator
            If `wav` is provided, reference and wav
        wav : iterator, optional

        """

        # === ready input data

        if wav is None and features is None:
            raise ValueError(
                'either `wav` or `features` must be provided.')

        # make a list from reference iterator
        # as it will be iterated at least twice
        reference = list(reference)

        # check provided annotations only contains speech/non_speech labels
        expected = set([self.SPEECH, self.NON_SPEECH])
        for annotation in reference:
            if set(annotation.labels()) != expected:
                raise ValueError(
                    ('reference must only contain '
                     '"%s" or "%s" labels.' % (self.SPEECH, self.NON_SPEECH))
                )

        # if features are not precomputed
        # create an iterator that does just that
        if features is None:
            features = itertools.imap(self.get_features, wav)

        # === actual HMM training

        self.hmm.fit(reference, features)

        return self

    def apply(self, wav=None, feature=None):
        """Perform speech activity detection on .wav file

        Parameters
        ----------
        wav : str, optional
            Path to processed .wav file.
        feature : SlidingWindowFeature, optional
            When provided, use precomputed `feature`.

        Returns
        -------
        speech : Timeline
            Speech segments.

        """
        if feature is None and wav is None:
            raise ValueError('Either wav or feature must be provided.')

        if feature is None:
            features = self.get_features(wav)

        detection = self.hmm.apply(features)

        return detection

    # Input/Output

    HMM = 'hmm'
    FEATURE = 'feature'
    CREATED = 'created'
    DESCRIPTION = 'description'

    def save(self, path, description=''):
        """Save model to file

        Parameters
        ----------
        path : str
        description : str, optional
            Optional description (e.g. of the training set)

        """

        data = {
            self.HMM: self.hmm,
            self.FEATURE: self.feature,
            self.CREATED: datetime.datetime.today(),
            self.DESCRIPTION: description,
        }

        with open(path, mode='w') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path, cache=False):
        """Load model from file

        Parameters
        ----------
        path : str
        cache : bool, optional
            Whether to cache feature extraction (True) or not (False).
            Defaults to False.
        """

        with open(path, mode='r') as f:
            data = pickle.load(f)

        sys.stdout.write('Created: %s\n' % data[cls.CREATED].isoformat())
        if data[cls.DESCRIPTION]:
            sys.stdout.write('Description: %s\n' % data[cls.DESCRIPTION])

        return cls(
            hmm=data[cls.HMM],
            feature=data[cls.FEATURE],
            cache=cache
        )


class SpeechTurnSegmentation(object):
    """Divergence-based speech turn segmentation


    Example
    -------

    >>> seg = SpeechTurnSegmentation()
    >>> seg.fit()
    >>> pathToWavFile = ''
    >>> annotation = seg.apply(pathToWavFile)

    Parameters
    ----------
    segmentation : SegmentationGaussianDivergence, optional
    duration : float, optional
    step : float, optional
    gap : float, optional
    threshold : float, optional
    feature : optional
        Defaults to MFCC with 12 coefficients, their delta, and delta energy.
    cache : bool, optional
        Whether to cache feature extraction (True) or not (False).
        Defaults to False.
    """

    def __init__(
        self,
        segmentation=None,
        duration=1., step=0.1, gap=0., threshold=0.,
        feature=None, cache=False
    ):

        super(SpeechTurnSegmentation, self).__init__()

        if segmentation is None:

            self.segmentation = SegmentationGaussianDivergence(
                duration=duration, step=step, gap=gap,
                threshold=threshold
            )

        else:

            self.segmentation = segmentation

        # default features for segmentation
        # are MFCC (energy + 12 coefficients)
        if feature is None:
            from pyannote.feature.yaafe import YaafeMFCC
            feature = YaafeMFCC(
                e=True, De=False, DDe=False,
                coefs=12, D=False, DD=False
            )
        self.feature = feature

        if cache:

            # initialize cache
            from joblib import Memory
            from tempfile import mkdtemp
            memory = Memory(cachedir=mkdtemp(), verbose=0)

            # cache feature extraction method
            self.get_features = memory.cache(self.get_features)

    def get_features(self, wav):
        return self.feature.extract(wav)

    def apply(self, wav=None, feature=None, speech=None):
        """Perform speech turn segmentation

        Parameters
        ----------
        wav : str, optional
            Path to processed .wav file.
        feature : SlidingWindowFeature, optional
            When provided, use precomputed `feature`.
        speech : Timeline, optional
            Speech segments.
        Returns
        -------
        speech : Timeline
            Speech segments.

        """
        if feature is None and wav is None:
            raise ValueError('Either wav or feature must be provided.')

        if feature is None:
            features = self.get_features(wav)

        segmentation = self.segmentation.apply(features)
        if speech is not None:
            segmentation = segmentation.crop(speech, mode='intersection')

        return segmentation

    # Input/Output

    SEGMENTATION = 'segmentation'
    FEATURE = 'feature'
    CREATED = 'created'
    DESCRIPTION = 'description'

    def save(self, path, description=''):
        """Save model to file

        Parameters
        ----------
        path : str
        description : str, optional
            Optional description (e.g. of the training set)

        """

        data = {
            self.SEGMENTATION: self.segmentation,
            self.FEATURE: self.feature,
            self.CREATED: datetime.datetime.today(),
            self.DESCRIPTION: description,
        }

        with open(path, mode='w') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path, cache=False):
        """Load model from file

        Parameters
        ----------
        path : str
        cache : bool, optional
            Whether to cache feature extraction (True) or not (False).
            Defaults to False.
        """

        with open(path, mode='r') as f:
            data = pickle.load(f)

        sys.stdout.write('Created: %s\n' % data[cls.CREATED].isoformat())
        if data[cls.DESCRIPTION]:
            sys.stdout.write('Description: %s\n' % data[cls.DESCRIPTION])

        return cls(
            segmentation=data[cls.SEGMENTATION],
            feature=data[cls.FEATURE],
            cache=cache
        )


class SpeakerIdentification(object):
    """Speaker identification based on GMM-UBM approach

    Example
    -------

    >>> sid = SpeakerIdentification(gmm_ubm)
    >>> sid.fit()
    >>> pathToWavFile = ''
    >>> annotation = sid.apply(pathToWavFile)

    Parameters
    ----------
    gmm_ubm : ClassificationGMMUBM
        GMM/UBM (pre-trained or not)
    feature : optional
        Defaults to MFCC with 13 coefficients, their delta, delta delta,
        delta energy and delta delta energy
    cache : bool, optional
        Whether to cache feature extraction (True) or not (False).
        Defaults to False.
    """

    def __init__(
        self,
        gmm_ubm,
        feature=None, cache=False
    ):

        super(SpeakerIdentification, self).__init__()

        self.gmm_ubm = gmm_ubm

        # default features for speaker identification are MFCC
        # 13 coefs + delta coefs  + delta delta coefs
        #          + delta energy + delta delta energy
        if feature is None:
            from pyannote.feature.yaafe import YaafeMFCC
            feature = YaafeMFCC(
                e=False, De=True, DDe=True,
                coefs=13, D=True, DD=True
            )
        self.feature = feature

        if cache:

            # initialize cache
            from joblib import Memory
            from tempfile import mkdtemp
            memory = Memory(cachedir=mkdtemp(), verbose=0)

            # cache feature extraction method
            self.get_features = memory.cache(self.get_features)

    @property
    def equal_priors(self):
        return self.gmm_ubm.equal_priors

    @equal_priors.setter
    def equal_priors(self, value):
        self.gmm_ubm.equal_priors = value

    @property
    def open_set(self):
        return self.gmm_ubm.open_set

    @open_set.setter
    def open_set(self, value):
        self.gmm_ubm.open_set = value

    def get_features(self, wav):
        return self.feature.extract(wav)

    def fit(self, reference, wav=None, features=None):
        """
        reference : iterator
            If `wav` is provided, reference and wav
        wav : iterator, optional

        """

        # === ready input data

        if wav is None and features is None:
            raise ValueError(
                'either `wav` or `features` must be provided.')

        # make a list from reference iterator
        # as it will be iterated at least twice
        reference = list(reference)

        # if features are not precomputed
        # create an iterator that does just that
        if features is None:
            features = itertools.imap(self.get_features, wav)

        # === actual GMM/UBM training

        self.gmm_ubm.fit(reference, features)

        return self

    def apply(self, speech_turns, wav=None, feature=None, probability=False):
        """Perform speaker identification on .wav file

        Parameters
        ----------
        speech_turns : Timeline or Annotation
            Pre-computed segmentation
        wav : str, optional
            Path to processed .wav file.
        feature : SlidingWindowFeature, optional
            When provided, use precomputed `feature`.
        probability : bool, optional
            If True, return posteriors (Scores) instead hard decision

        Returns
        -------
        results : `Annotation` or `Scores`
            If probability is True, return posterior probabilities.
            If probability is False (default), return identity annotation.

        """

        if feature is None and wav is None:
            raise ValueError('Either wav or feature must be provided.')

        if feature is None:
            features = self.get_features(wav)

        if probability:
            return self.gmm_ubm.predict_proba(speech_turns, features)
        else:
            return self.gmm_ubm.predict(speech_turns, features)

    # Input/Output

    GMMUBM = 'gmm_ubm'
    FEATURE = 'feature'
    CREATED = 'created'
    DESCRIPTION = 'description'

    def save(self, path, description=''):
        """Save model to file

        Parameters
        ----------
        path : str
        description : str, optional
            Optional description (e.g. of the training set)

        """

        data = {
            self.GMMUBM: self.gmm_ubm,
            self.FEATURE: self.feature,
            self.CREATED: datetime.datetime.today(),
            self.DESCRIPTION: description,
        }

        with open(path, mode='w') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path, cache=False):
        """Load model from file

        Parameters
        ----------
        path : str
        cache : bool, optional
            Whether to cache feature extraction (True) or not (False).
            Defaults to False.
        """

        with open(path, mode='r') as f:
            data = pickle.load(f)

        sys.stdout.write('Created: %s\n' % data[cls.CREATED].isoformat())
        if data[cls.DESCRIPTION]:
            sys.stdout.write('Description: %s\n' % data[cls.DESCRIPTION])

        return cls(
            data[cls.GMMUBM],
            feature=data[cls.FEATURE],
            cache=cache
        )
