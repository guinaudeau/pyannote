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

class BaseModelMixin(object):
    """
    Clustering model mixin
    
    """
    def mmx_setup(self, **kwargs):
        """
        Setup model internal variables
        """
        pass
    
    def mmx_fit(self, label, **kwargs):
        """
        Create model
        
        Parameters
        ----------
        label : any valid label
            The `label` to model
        
        Returns
        -------
        model : any object
            The model for `label`
        
        """
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_fit()' % name)
    
    def mmx_symmetric(self):
        """
        Is model similarity symmetric?
        
        Returns
        -------
        symmetric: bool
            True if similarity is symmetric, False otherwise.
        
        """
        return False
    
    def mmx_compare(self, label, other_label, **kwargs):
        """
        Similarity between two labels
        
        Parameters
        ----------
        label, other_label : any valid label
            The labels to compare
            
        Returns
        -------
        similarity : float
            Similarity between the two labels, the higher the more similar
        
        """
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_compare()' % name)
    
    def mmx_merge(self, labels, **kwargs):
        """
        Merge models
        
        Parameters
        ----------
        labels : list of valid labels
            The labels whose models should be merged
            
        Returns
        -------
        model : any object
            The merged models
        
        """
        name = self.__class__.__name__
        raise NotImplementedError('%s sub-class must implement method'
                                  'mmx_merge()' % name)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
