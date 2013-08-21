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

import numpy as np
import pandas


class LabelMatrix(object):

    def __init__(self, data=None, dtype=None, rows=None, columns=None):
        super(LabelMatrix, self).__init__()
        if data is None and dtype is None:
            dtype = np.float
        self.df = pandas.DataFrame(
            data=data, dtype=dtype, index=rows, columns=columns)

    def __setitem__(self, (row, col), value):
        self.df = self.df.set_value(row, col, value)
        return self

    def __getitem__(self, (row, col)):
        return self.df.at[row, col]

    def get_rows(self):
        return list(self.df.index)

    def get_columns(self):
        return list(self.df.columns)

    def __get_shape(self):
        return self.df.shape
    shape = property(fget=__get_shape)

    def __nonzero__(self):
        N, M = self.df.shape
        return N*M != 0

    def iter_values(self):
        for row in self.get_rows():
            for col in self.get_columns():
                val = self.df.at[row, col]
                if not np.isnan(val):
                    yield row, col, val

    def argmax(self, axis=None):
        """
        Labels of the maximum values along an axis.

        Parameters
        ----------
        axis : int, optional
            By default, labels are into the whole matrix, otherwise
            along the specified axis (rows or columns)

        Returns
        -------
        label_dict : dictionary of labels
            Dictionary of labels into the matrix.
            {col_label : max_row_label} if axis == 0
            {row_label : max_col_label} if axis == 1
            {max_row_label : max_col_label} if axis == None
        """

        if axis == 0:
            return {c: r
                    for (c, r) in self.df.idxmax(axis=axis).iteritems()}

        elif axis == 1:
            return {r: c
                    for (r, c) in self.df.idxmax(axis=axis).iteritems()}

        else:
            values = [
                (_r, _c, self.df.loc[_r, _c])
                for (_c, _r) in self.df.idxmax(axis=0).iteritems()
            ]
            r, c, _ = sorted(values, key=lambda v: v[2])[-1]
            return {r: c}

    def __neg__(self):
        negated = LabelMatrix()
        negated.df = -self.df
        return negated

    def argmin(self, axis=None):
        """
        Labels of the minimum values along an axis.

        Parameters
        ----------
        axis : int, optional
            By default, labels are into the whole matrix, otherwise
            along the specified axis (rows or columns)

        Returns
        -------
        label_dict : dictionary of labels
            Dictionary of labels into the matrix.
            {col_label : max_row_label} if axis == 0
            {row_label : max_col_label} if axis == 1
            {max_row_label : max_col_label} if axis == None
        """

        return (-self).argmax(axis=axis)

    def __get_T(self):
        transposed = LabelMatrix()
        transposed.df = self.df.T
        return transposed
    T = property(fget=__get_T)

    def remove_column(self, col):
        del self.df[col]
        return self

    def remove_row(self, row):
        df = self.df.T
        del df[row]
        self.df = df.T
        return self

    def copy(self):
        copied = LabelMatrix()
        copied.df = self.df.copy()
        return copied

    def subset(self, rows=None, columns=None):

        if rows is None:
            rows = set(self.get_rows())

        if columns is None:
            columns = set(self.get_columns())

        remove_rows = set(self.get_rows()) - rows
        remove_columns = set(self.get_columns()) - columns

        copied = self.copy()
        for row in remove_rows:
            copied = copied.remove_row(row)
        for col in remove_columns:
            copied = copied.remove_column(col)

        return copied

    def __gt__(self, value):
        compared = LabelMatrix()
        compared.df = self.df > value
        return compared

    # def sum(self, axis=None):
    #     summed = LabelMatrix()
    #     summed.df = self.df.sum(axis=axis)
    #     return summed

    def __str__(self):
        return str(self.df)


# class LabelMatrix2(pandas.DataFrame):

#     def get_rows(self):
#         return list(self.index)

#     def get_columns(self):
#         return list(self.columns)

#     def __nonzero__(self):
#         n, m = self.shape
#         return n*m != 0

#     # def __getitem__(self, key):
#     #     row = key[0]
#     #     col = key[1]
#     #     return self.at[row, col]

#     # def __setitem__(self, key, value):
#     #     row = key[0]
#     #     col = key[1]
#     #     self = self.set_value(row, col, value)

#     def iter_values(self):
#         """
#         """
#         for row in self.get_rows():
#             for col in self.get_columns():
#                 val = self.at[row, col]
#                 if not np.isnan(val):
#                     yield row, col, val

#     def argmax(self, axis=None):
#         """
#         Labels of the maximum values along an axis.

#         Parameters
#         ----------
#         axis : int, optional
#             By default, labels are into the whole matrix, otherwise
#             along the specified axis (rows or columns)

#         Returns
#         -------
#         label_dict : dictionary of labels
#             Dictionary of labels into the matrix.
#             {col_label : max_row_label} if axis == 0
#             {row_label : max_col_label} if axis == 1
#             {max_row_label : max_col_label} if axis == None
#         """

#         if axis == 0:
#             return {c: r
#                     for (c, r) in self.idxmax(axis=axis).iteritems()}

#         elif axis == 1:
#             return {r: c
#                     for (r, c) in self.idxmax(axis=axis).iteritems()}

#         else:
#             values = [
#                 (_r, _c, self.loc[_r, _c])
#                 for (_c, _r) in self.idxmax(axis=0).iteritems()
#             ]
#             r, c, _ = sorted(values, key=lambda v: v[2])[-1]
#             return {r: c}

#     def argmin(self, axis=None):
#         """
#         Labels of the minimum values along an axis.

#         Parameters
#         ----------
#         axis : int, optional
#             By default, labels are into the whole matrix, otherwise
#             along the specified axis (rows or columns)

#         Returns
#         -------
#         label_dict : dictionary of labels
#             Dictionary of labels into the matrix.
#             {col_label : max_row_label} if axis == 0
#             {row_label : max_col_label} if axis == 1
#             {max_row_label : max_col_label} if axis == None
#         """

#         return (-self).argmax(axis=axis)

#     def remove_column(self, col):
#         del self[col]
#         return self

#     def remove_row(self, row):
#         return self.T.remove_column(row).T

#     def subset(self, rows=None, columns=None):

#         if rows is None:
#             rows = set(self.get_rows())

#         if columns is None:
#             columns = set(self.get_columns())

#         remove_rows = set(self.get_rows()) - rows
#         remove_columns = set(self.get_columns()) - columns

#         copied = self.copy()
#         for row in remove_rows:
#             copied = copied.remove_row(row)
#         for col in remove_columns:
#             copied = copied.remove_column(col)

#         return copied

def get_cooccurrence_matrix(R, C):

    rows = R.labels()
    cols = C.labels()
    nRows = len(rows)
    nCols = len(cols)

    K = np.zeros((nRows, nCols), dtype=np.float)
    for r, row in enumerate(rows):
        row_coverage = R.label_coverage(row)
        for c, col in enumerate(cols):
            col_coverage = C.label_coverage(col)
            coverage = row_coverage.crop(col_coverage, mode='intersection')
            K[r, c] = coverage.duration()

    return LabelMatrix(data=K, rows=rows, columns=cols)


from pyannote.base.segment import SEGMENT_PRECISION


def get_tfidf_matrix(words, documents, idf=True, log=False):
    """Term Frequency Inverse Document Frequency (TF-IDF) confusion matrix

    C[i, j] = TF(i, j) x IDF(i) where
        - documents are J labels
        - words are co-occurring I labels

                  duration of word i in document j         confusion[i, j]
    TF(i, j) = --------------------------------------- = -------------------
               total duration of I words in document j   sum confusion[:, j]

                        number of J documents
    IDF(i) = ----------------------------------------------
             number of J documents co-occurring with word i

                      Nj
           = -----------------------
             sum confusion[i, :] > 0

    Parameters
    ---------
    words : :class:`pyannote.base.annotation.Annotation`
        Every label occurrence is considered a word
        (weighted by the duration of the segment)
    documents : :class:`pyannote.base.annotation.Annotation`
        Every label is considered a document.
    idf : bool, optional
        If `idf` is set to True, returns TF x IDF.
        Otherwise, returns TF. Default is True
    log : bool, optional
        If `log` is True, returns TF x log IDF
    """
    M = get_cooccurrence_matrix(words, documents)
    Nw, Nd = M.shape

    if Nd == 0:
        return M

    K = M.df.values
    rows = M.get_rows()
    cols = M.get_columns()

    # total duration of all words cooccurring with each document
    # np.sum(self.M, axis=0)[j] = 0 ==> self.M[i, j] = 0 for all i
    # so we can safely use np.maximum(1e-3, ...) to avoid DivideByZero
    tf = K / np.tile(
        np.maximum(SEGMENT_PRECISION, np.sum(K, axis=0)),
        (Nw, 1)
    )

    # use IDF only if requested (default is True ==> use IDF)
    if idf:

        # number of documents cooccurring with each word
        # np.sum(self.M > 0, axis=1)[i] = 0 ==> tf[i, j] = 0 for all i
        # and therefore tf.idf [i, j ] = 0
        # so we can safely use np.maximum(1, ...) to avoid DivideByZero
        idf = np.tile(
            float(Nd) / np.maximum(1, np.sum(K > 0, axis=1)),
            (Nd, 1)).T

        # use log only if requested (defaults is False ==> do not use log)
        if log:
            idf = np.log(idf)

    else:
        idf = 1.

    return LabelMatrix(data=tf * idf, rows=rows, columns=cols)

# class AutoCooccurrence(Cooccurrence):
#     """
#     Auto confusion matrix

#     Parameters
#     ----------
#     I : Annotation

#     neighborhood : float, optional

#     Examples
#     --------

#     >>> M = AutoCooccurrence(A, neighborhood=10)

#     Get total confusion duration (in seconds) between id_A and id_B::

#     >>> confusion = M[id_A, id_B]

#     Get confusion dictionary for id_A::

#     >>> confusions = M(id_A)


#     """
#     def __init__(self, I, neighborhood=0.):

# extend each segment on left and right by neighborhood seconds
#         segment_func = lambda s : neighborhood << s >> neighborhood
#         xI = I.copy(segment_func=map_func)

# auto-cooccurrence
#         super(AutoCooccurrence, self).__init__(xI, xI)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
