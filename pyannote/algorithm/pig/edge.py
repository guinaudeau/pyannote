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

import pickle
import logging
import datetime
import itertools
import numpy as np
from pyannote import Segment

from pyannote.algorithm.pig.pig import PersonInstanceGraph
from pyannote.algorithm.pig.vertex import InstanceVertex

from pyannote.base.annotation import Unknown
from pyannote.base.matrix import LabelMatrix
from pyannote.algorithm.calibration.clustering import ClusteringCalibration


class PIGIntraModalEdges(object):
    """Intra-modal edges generator

    Parameters
    ----------
    prior : float, optional
        prior probability that two instance vertices are from the same person.
        By default, `prior` is set to the one estimated using fit.
    calibration : {'linear', 'isotonic'}
    model : HACModel, optional
        This model is used only in case

    """

    def __init__(self, calibration='linear', model=None, prior=None):

        super(PIGIntraModalEdges, self).__init__()
        self.model = model
        self.calibration = ClusteringCalibration(method=calibration)
        self.prior = prior

    def get_groundtruth_matrix(self, annotation):
        """

        Parameters
        ----------
        annotation : `Annotation`

        Returns
        -------
        matrix : LabelMatrix
            Square matrix indexed by instance vertices (one for each track)
            . 1 if instance vertices are the same person
            . 0 if instance vertices are two different persons
            . np.NaN if unsure
        """

        tracks = [
            (segment, track)
            for segment, track in annotation.itertracks()
        ]

        groundtruth = LabelMatrix(
            rows=tracks, columns=tracks,
            dtype=np.float
        )

        for s, t, l in annotation.itertracks(label=True):

            v = (s, t)

            for s_, t_, l_ in annotation.itertracks(label=True):

                v_ = (s_, t_)

                if isinstance(l, Unknown) or isinstance(l_, Unknown):
                    g = np.NaN
                else:
                    g = 1 if l == l_ else 0

                groundtruth[v, v_] = g

        return groundtruth

    def fit(self, reference, similarity=None, features=None):
        """

        Parameters
        ----------

        reference : iterator
            Generates labeled annotations
        similarity : iterator, optional
            Generates track similarity matrices
        features : iterator, optional

        """

        if similarity is None and features is None:
            raise ValueError(
                'either `similarity` or `features` must be provided.')

        # make reference a list because it will be iterated at least twice
        reference = list(reference)

        # if track similarity matrices are not provided,
        # try to compute it on the fly using provided model
        if similarity is None:
            similarity = [
                self.model.get_track_similarity_matrix(r, f)
                for r, f in itertools.izip(reference, features)
            ]

        # groundtruth instance vertices clustering matrices
        groundtruth = itertools.imap(
            self.get_groundtruth_matrix,
            reference
        )

        self.calibration.fit(groundtruth, similarity)

        return self

    def __call__(self, annotation, similarity=None, features=None):

        modality = annotation.modality
        uri = annotation.uri

        if similarity is None:
            similarity = self.model.get_track_similarity_matrix(
                annotation, features)

        probs = self.calibration.apply(similarity, prior=self.prior)

        for (s1, t1), (s2, t2), p in probs.itervalues():
            v1 = InstanceVertex(
                segment=s1, track=t1, modality=modality, uri=uri)
            v2 = InstanceVertex(
                segment=s2, track=t2, modality=modality, uri=uri)
            yield v1, v2, p

    CALIBRATION = 'calibration'
    MODEL = 'model'
    PRIOR = 'prior'
    CREATED = 'created'
    DESCRIPTION = 'description'

    def save(self, path, description=''):
        """Save to file

        Parameters
        ----------
        path : str
        description : str, optional
            Optional description (e.g. of the training set)
        """

        data = {
            self.CALIBRATION: self.calibration,
            self.MODEL: self.model,
            self.PRIOR: self.prior,
            self.CREATED: datetime.datetime.today(),
            self.DESCRIPTION: description,
        }

        with open(path, mode='w') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path):
        """Load from file

        Parameters
        ----------
        path : str
        """

        with open(path, mode='r') as f:
            data = pickle.load(f)

        # --- logging -----------------------------------------------------
        logging.info('Created: %s' % data[cls.CREATED].isoformat())
        if data[cls.DESCRIPTION]:
            logging.info('Description: %s' % data[cls.DESCRIPTION])
        # -----------------------------------------------------------------

        intraModelEdges = cls(
            model=data[cls.MODEL],
            prior=data[cls.PRIOR]
        )

        intraModelEdges.calibration = data[cls.CALIBRATION]

        return intraModelEdges



class PIGCrossModalEdges(object):
    """

    Parameters
    ----------
    resolution : float, optional
        Time resolution in second. Defaults to 0.1 second.
    neighbourhood : float, optional
    modality1, modality2 : str, optional
        Connected modalities
    """
    def __init__(
        self,
        resolution=0.1, neighbourhood=30.,
        modality1=None, modality2=None
    ):
        super(PIGCrossModalEdges, self).__init__()
        self.resolution = resolution
        self.neighbourhood = neighbourhood
        self.modality1 = modality1
        self.modality2 = modality2

    def get_indicator_function(self, annotation, extent):
        """
        Parameters
        ----------
        annotation : `Annotation`
        extent : `Segment`

        Returns
        -------
        """
        n = extent.duration / self.resolution
        counts = np.zeros(n)

        cropped = annotation.crop(extent, mode='intersection')
        for segment, _ in cropped.itertracks():
            start = (segment.start - extent.start) / self.resolution
            end = (segment.end - extent.start) / self.resolution
            counts[start:end] += 1.

        return counts

    def fit(self, modality1, modality2):
        """
        Parameters
        ----------
        modality1, modality2: `Annotation` iterators
        """

        #
        width = int(self.neighbourhood/self.resolution)
        num = np.zeros(2*width+1, dtype=np.float)
        den = np.zeros(2*width+1, dtype=np.float)
        for annotation1, annotation2 in itertools.izip(modality1, modality2):

            # --- logging -----------------------------------------------------
            uri = annotation1.uri
            logging.debug("PIGCrossModalEdges -- fit -- %s" % uri)
            # -----------------------------------------------------------------

            if self.modality1 is None:
                self.modality1 = annotation1.modality

            if self.modality2 is None:
                self.modality2 = annotation2.modality

            assert annotation1.modality == self.modality1
            assert annotation2.modality == self.modality2

            if not annotation1 or not annotation2:
                continue

            extent = (
                annotation1.get_timeline().extent() |
                annotation2.get_timeline().extent()
            )

            # all1 = self.get_indicator_function(annotation1, extent) > 0
            all2 = self.get_indicator_function(annotation2, extent) > 0
            for label in annotation1.labels():

                a1 = annotation1.subset(set([label]))
                one1 = self.get_indicator_function(a1, extent) > 0

                a2 = annotation2.subset(set([label]))
                one2 = self.get_indicator_function(a2, extent) > 0

                for delta in range(1, width+1):
                    num[width+delta] += np.sum(one1[:-delta] * one2[delta:])
                    den[width+delta] += np.sum(one1[:-delta] * all2[delta:])
                    num[width-delta] += np.sum(one1[delta:] * one2[:-delta])
                    den[width-delta] += np.sum(one1[delta:] * all2[:-delta])

                num[width] += np.sum(one1 * one2)
                den[width] += np.sum(one1 * all2)

        self.probability = num / den

        return self

    def get_probability(self, segment1, segment2):

        width = int(self.neighbourhood/self.resolution)
        counts = np.zeros(2*width+1, dtype=np.float)

        for t1 in range(
            int(segment1.start/self.resolution),
            int(segment1.end/self.resolution)
        ):

            s2 = int(segment2.start/self.resolution)
            e2 = int(segment2.end/self.resolution)

            counts[width+s2-t1:width+e2-t1] += 1

        return np.average(self.probability, weights=counts)

    def __call__(self, modality1, modality2):

        assert modality1.uri == modality2.uri
        assert modality1.modality == self.modality1
        assert modality2.modality == self.modality2

        uri = modality1.uri

        for segment1, track1 in modality1.itertracks():

            v1 = InstanceVertex(
                segment=segment1, track=track1,
                modality=self.modality1, uri=uri
            )

            roi = Segment(
                start=segment1.start - self.neighbourhood,
                end=segment1.end + self.neighbourhood
            )

            neighbourhood = modality2.crop(roi, mode='strict')
            for segment2, track2 in neighbourhood.itertracks():

                v2 = InstanceVertex(
                    segment=segment2, track=track2,
                    modality=self.modality2, uri=uri
                )

                p = self.get_probability(segment1, segment2)

                yield v1, v2, p


    RESOLUTION = 'resolution'
    NEIGHBOURHOOD = 'neighbourhood'
    PROB = 'probability'
    MODALITY1 = 'modality1'
    MODALITY2 = 'modality2'
    CREATED = 'created'
    DESCRIPTION = 'description'

    def save(self, path, description=''):
        """Save to file

        Parameters
        ----------
        path : str
        description : str, optional
            Optional description (e.g. of the training set)
        """

        data = {
            self.RESOLUTION: self.resolution,
            self.NEIGHBOURHOOD: self.neighbourhood,
            self.PROB: self.probability,
            self.MODALITY1: self.modality1,
            self.MODALITY2: self.modality2,
            self.CREATED: datetime.datetime.today(),
            self.DESCRIPTION: description,
        }

        with open(path, mode='w') as f:
            pickle.dump(data, f)

    @classmethod
    def load(cls, path):
        """Load from file

        Parameters
        ----------
        path : str
        """

        with open(path, mode='r') as f:
            data = pickle.load(f)

        # --- logging -----------------------------------------------------
        logging.info('Created: %s' % data[cls.CREATED].isoformat())
        if data[cls.DESCRIPTION]:
            logging.info('Description: %s' % data[cls.DESCRIPTION])
        # -----------------------------------------------------------------

        crossModalEdges = cls(
            resolution=data[cls.RESOLUTION],
            neighbourhood=data[cls.NEIGHBOURHOOD],
            modality1=data[cls.MODALITY1],
            modality2=data[cls.MODALITY2]
        )

        crossModalEdges.probability = data[cls.PROB]

        return crossModalEdges


class PIGIdentificationEdges(object):

    def __init__(self):
        super(PIGIdentificationEdges, self).__init__()

    def fit(self, scores_iterator, reference_iterator):
        for scores, reference in itertools.izip(
            scores_iterator, reference_iterator
        ):
            pass

    def apply(self, scores):

        pig = PersonInstanceGraph()
        pig.add_scores(self.calibration.apply(scores))
        return pig
