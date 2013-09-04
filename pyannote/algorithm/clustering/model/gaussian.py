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


from pyannote.algorithm.clustering.model.base import BaseModelMixin
from pyannote.stats.gaussian import Gaussian


class GaussianMMx(BaseModelMixin):
    """Mono-gaussian model mixin

    Parameter
    ---------
    covariance_type : {'diag', 'full'}, optional
        Default is 'full' covariance matrix.
    """

    def mmx_setup(self, covariance_type='full', **kwargs):
        """Model mixin setup

        Parameters
        ----------
        covariance_type : {'diag', 'full'}, optional
            Default is 'full' covariance matrix.
        """
        self.mmx_covariance_type = covariance_type

    def mmx_fit(self, label, annotation=None, feature=None, **kwargs):
        """Fit one gaussian to label features

        Parameters
        ----------
        label : hashable object
            A label existing in processed `annotation`
        annotation : :class:`Annotation`, optional
            If not provided, use self.annotation instead
        feature : :class:`Feature`, optional
            If not provided, use self.feature instead


        Returns
        -------
        g : :class:`pyannote.stats.gaussian.Gaussian`
            A Gaussian fitted to label features

        """

        if annotation is None:
            annotation = self.annotation

        if feature is None:
            feature = self.feature

        # extract features for this label
        data = feature.crop(annotation.label_timeline(label))
        # fit gaussian and return it
        return Gaussian(covariance_type=self.mmx_covariance_type).fit(data)

    def mmx_merge(self, labels, models=None, **kwargs):
        """Merge Gaussians

        Merge multiple labels into one.

        Parameters
        ----------
        labels :
        models :
            If not provided, use self.models

        """

        if models is None:
            models = self.models

        # start with first model
        new_model = models[labels[0]]

        # merge all the others the one after the others
        for label in labels[1:]:
            new_model = new_model.merge(models[label])

        return new_model


class BICMMx(GaussianMMx):
    """Bayesian Information Criterion model mixin

    Parameters
    ----------
    covariance_type : {'diag', 'full'}, optional
        Default is 'full' covariance matrix.
    penalty_coef : float, optional
        Coefficient for size model penalty. Default is 3.5

    """

    def mmx_setup(self, covariance_type='full', penalty_coef=3.5, **kwargs):
        """Model mixin setup

        Parameters
        ----------
        covariance_type : {'diag', 'full'}, optional
            Default is 'full' covariance matrix.
        penalty_coef : float, optional
            Coefficient for size model penalty. Default is 3.5
        """
        super(BICMMx, self).mmx_setup(covariance_type=covariance_type)
        self.mmx_penalty_coef = penalty_coef

    def mmx_symmetric(self):
        return True

    def mmx_compare(self, label, other_label, models=None, **kwargs):
        """Compute dBIC

        Parameters
        ----------
        models :
            If not provided, use self.models

        See also
        --------
        :meth:`pyannote.stats.gaussian.Gaussian.bic`

        """
        if models is None:
            models = self.models

        model = models[label]
        other_model = models[other_label]

        dissimilarity, _ = model.bic(
            other_model, penalty_coef=self.mmx_penalty_coef
        )

        return (-dissimilarity)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
