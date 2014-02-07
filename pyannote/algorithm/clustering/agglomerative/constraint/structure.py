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


from pyannote.base.matrix import LabelMatrix, get_cooccurrence_matrix
from pyannote.algorithm.clustering.agglomerative.constraint.base import BaseConstraintMixin


class CooccurringCMx(object):
    """
    Two cooccurring labels cannot be merged
    """
    def cmx_setup(self, **kwargs):
        pass

    def cmx_init(self):
        """
        Two cooccurring labels cannot be
        """

        # create new annotation where each segment
        # is slightly extended on both ends
        self.cmx_xann = self.annotation.copy(segment_func=self.cmx_xsegment)

        # compute labels cooccurrence matrix
        M = get_cooccurrence_matrix(self.annotation, self.annotation)
        self.cmx_cooccurring = M > 0.

    def cmx_update(self, new_label, merged_labels):

        # remove rows and columns for old labels
        for label in merged_labels:
            if label == new_label:
                continue
            self.cmx_cooccurring.remove_row(label)
            self.cmx_cooccurring.remove_column(label)

        # compute cooccurrence matrix with new_label
        M = get_cooccurrence_matrix(
            self.annotation.subset(set([new_label])),
            self.annotation
        )

        # update cooccurring matrix accordingly
        labels = self.annotation.labels()
        for label in labels:
            if label == new_label:
                continue
            self.cmx_cooccurring[new_label, label] = M[new_label, label] > 0.
            self.cmx_cooccurring[label, new_label] = M[new_label, label] > 0.

    def cmx_meet(self, labels):
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                if self.cmx_cooccurring[label, other_label]:
                    return False
        return True


class ContiguousCMx(BaseConstraintMixin):
    """
    Two labels are mergeable if they are contiguous
    """

    def cmx_setup(self, tolerance=0., **kwargs):
        self.cmx_tolerance = tolerance
        self.cmx_xsegment = lambda s: .5*tolerance << s >> .5*tolerance

    def cmx_init(self):
        """
        Two labels are mergeable if they are contiguous
        """

        # create new annotation where each segment
        # is slightly extended on both ends
        self.cmx_xann = self.annotation.copy(segment_func=self.cmx_xsegment)

        # compute labels cooccurrence matrix
        # cooccurring labels can be merged (they're contiguous)-- others cannot
        M = get_cooccurrence_matrix(self.cmx_xann, self.cmx_xann)
        ilabels, jlabels = M.labels
        self.cmx_contiguous = LabelMatrix(ilabels=ilabels, jlabels=jlabels,
                                          Mij = M.M > 0, dtype=bool,
                                          default=False)

    def cmx_update(self, new_label, merged_labels):

        # update labels in extended annotation
        translation = {old_label : new_label for old_label in merged_labels}
        self.cmx_xann = self.cmx_xann % translation

        # remove rows and columns for old labels
        for label in merged_labels:
            if label == new_label:
                continue
            self.cmx_contiguous.remove_row(label)
            self.cmx_contiguous.remove_column(label)

        # compute cooccurrence matrix with new_label
        M = get_cooccurrence_matrix(self.cmx_xann(new_label), self.cmx_xann)

        # update contiguous_matrix accordingly
        labels = self.annotation.labels()
        for label in labels:
            if label == new_label:
                continue
            self.cmx_contiguous[new_label, label] = M[new_label, label] > 0.
            self.cmx_contiguous[label, new_label] = M[new_label, label] > 0.

    def cmx_meet(self, labels):
        for l, label in enumerate(labels):
            for other_label in labels[l+1:]:
                if not self.cmx_contiguous[label, other_label]:
                    return False
        return True


# class XTagsCMx(BaseConstraintMixin):
#
#     def cmx_init(self, xtags=None, **kwargs):
#         """
#         """
#
#         # keep track
#         self.cmx_xtags = xtags
#         self.cmx_conflicting_xtags = LabelMatrix(dtype=bool, default=False)
#         labels = self.annotation.labels()
#         for l, label in enumerate(labels):
#
#             # set of tags intersecting label
#             cov = self.annotation.label_coverage(label)
#             tags = set(self.cmx_xtags.crop(cov, mode='loose').labels())
#
#             for other_label in labels[l+1:]:
#
#                 # set of tags intersecting other label
#                 other_cov = self.annotation.label_coverage(other_label)
#                 other_tags = set(self.cmx_xtags.crop(other_cov, mode='loose').labels())
#
#                 # are there any tag conflicts?
#                 conflicting_xtags = bool(tags ^ other_tags)
#                 self.cmx_conflicting_xtags[other_label, label] = conflicting_xtags
#                 self.cmx_conflicting_xtags[label, other_label] = conflicting_xtags
#
#     def cmx_update(self, new_label, merged_labels):
#
#         # remove rows and columns for old labels
#         for label in merged_labels:
#             if label == new_label:
#                 continue
#             del self.cmx_conflicting_xtags[label, :]
#             del self.cmx_conflicting_xtags[:, label]
#
#         # set of tags intersecting new label
#         cov = self.annotation.label_coverage(new_label)
#         tags = set(self.cmx_xtags.crop(cov, mode='loose').labels())
#
#         # update row and column for new label
#         labels = self.annotation.labels()
#
#         for label in labels:
#
#             if label == new_label:
#                 continue
#
#             # set of tags intersection other label
#             other_cov = self.annotation.label_coverage(label)
#             other_tags = set(self.cmx_xtags.crop(other_cov, mode='loose').labels())
#
#             # are there any tag conflicts
#             conflicting_xtags = bool(tags ^ other_tags)
#             self.cmx_conflicting_xtags[new_label, label] = conflicting_xtags
#             self.cmx_conflicting_xtags[label, new_label] = conflicting_xtags
#
#     def cmx_meet(self, labels):
#         for l, label in enumerate(labels):
#             for other_label in labels[l+1:]:
#                 if self.cmx_conflicting_xtags[label, other_label]:
#                     return False
#         return True
#

if __name__ == "__main__":
    import doctest
    doctest.testmod()
