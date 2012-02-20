#!/usr/bin/env python
# encoding: utf-8
    

class NoMatch(object):
    """
    """
    
    nextID = 0
    """
    Keep track of the number of instances since last reset
    """
    
    @classmethod
    def reset(cls):
        cls.nextID = 0
    
    @classmethod
    def next(cls):
        cls.nextID += 1
        return cls.nextID
        
    def __init__(self, format='NoMatch%03d'):
        super(NoMatch, self).__init__()
        self.ID = NoMatch.next()
        self.format = format
    
    def __str__(self):
        return self.format % self.ID
    
    def __repr__(self):
        return 'NoMatch'
        
    def __hash__(self):
        return hash(self.ID)
        
    def __eq__(self, other):
        if isinstance(other, NoMatch):
            return self.ID == other.ID
        else:
            return False

class MElement(object):
    
    def __init__(self, modality, element):
        super(MElement, self).__init__()
        self.modality = modality
        self.element = element
        
    def __eq__(self, other):
        return (self.element == other.element) & \
               (self.modality == other.modality)
    
    def __hash__(self):
        return hash(self.element)
        
    def __str__(self):
        return '%s (%s)' % (self.element, self.modality)
        
    def __repr__(self):
        return str(self)

class Mapping(object):
    
    def __init__(self, modality1, modality2):
        super(Mapping, self).__init__()
        self.__modality1 = modality1
        self.__modality2 = modality2

        self._one1_to_many2 = {}
        self.__one2_to_many1 = {}
        self._many1_to_many2 = {}
    
    def __get_modality1(self): 
        return self.__modality1
    modality1 = property(fget=__get_modality1, \
                     fset=None, \
                     fdel=None, \
                     doc="First modality.")

    def __get_modality2(self): 
        return self.__modality2
    modality2 = property(fget=__get_modality2, \
                     fset=None, \
                     fdel=None, \
                     doc="Second modality.")
    
    def __get_first_set(self):
        return set(self._one1_to_many2.keys())
    first_set = property(fget=__get_first_set, \
                        fset=None, \
                        fdel=None, \
                        doc="First set.")

    def __get_second_set(self):
        return set(self.__one2_to_many1.keys())
    second_set = property(fget=__get_second_set, \
                        fset=None, \
                        fdel=None, \
                        doc="Second set.")
    
    def _check_mapping(self, mapping):
        
        # expected mapping
        # (elements1, elements2)
        # with elements1 = [a, b, c]
        #      elements2 = [d, e]
        if (not isinstance(mapping, tuple)) or (not len(mapping) == 2):
            raise ValueError('')
        
        elements1 = mapping[0]
        elements2 = mapping[1]
        
        if elements1 is None:
            elements1 = tuple([NoMatch()])
        
        if elements2 is None:
            elements2 = tuple([NoMatch()])
        
        if not isinstance(elements1, (list, tuple, set)):
            raise ValueError('Left mapping part (%s) must be a list, tuple or set.' % (elements1))
            
        if not isinstance(elements2, (list, tuple, set)):
            raise ValueError('Right mapping part (%s) must be a list, tuple or set' % (elements2))
        
        return tuple(elements1), tuple(elements2)
    
    def __iadd__(self, mapping):
        
        elements1, elements2 = self._check_mapping(mapping)
        
        already_mapped = set(elements1) & set(self._one1_to_many2)
        if already_mapped:
            already_mapped = already_mapped.pop()
            raise ValueError('%s (%s) is already mapped to %s.' % \
                             (already_mapped, self.__modality1, self._one1_to_many2[already_mapped]))
            
        already_mapped = set(elements2) & set(self.__one2_to_many1)
        if already_mapped:
            already_mapped = already_mapped.pop()
            raise ValueError('%s (%s) is already mapped to %s.' % \
                             (already_mapped, self.__modality2, self.__one2_to_many1[already_mapped]))
        
        for elt1 in elements1:
            self._one1_to_many2[elt1] = elements2
        for elt2 in elements2:
            self.__one2_to_many1[elt2] = elements1
        
        self._many1_to_many2[elements1] = elements2
        
        return self
        
    def to_partition(self):
        partition = {}
        C = 0
        for left, right in self:
            partition.update({MElement(self.modality1, element): C for element in left \
                                                                   if not isinstance(element, NoMatch)} )
            partition.update({MElement(self.modality2, element): C for element in right \
                                                                   if not isinstance(element, NoMatch)} )
            C += 1
        return partition
        
    def to_expected_partition(self):
        
        left = set([element for element in self._one1_to_many2 if not isinstance(element, NoMatch)])
        right = set([element for element in self.__one2_to_many1 if not isinstance(element, NoMatch)])
        expected = {element:e for e, element in enumerate(left | right)}

        partition = {}
        for element in left:
            partition[MElement(self.modality1, element)] = expected[element]
        for element in right:
            partition[MElement(self.modality2, element)] = expected[element]
        
        return partition
        
    def to_dict(self, reverse=False):
        if reverse:
            return {right:left for left, right in self}
        else:
            return {left:right for left, right in self}
    
    def to_expected_dict(self, reverse=False):
        
        left = set([element for element in self._one1_to_many2 if not isinstance(element, NoMatch)])
        right = set([element for element in self.__one2_to_many1 if not isinstance(element, NoMatch)])
        both = left & right
        
        expected_dict = {}
        for element in both:
            expected_dict[element] = element
        for element in left-both:
            expected_dict[element] = NoMatch()
        for element in right-both:
            expected_dict[NoMatch()] = element
        
        if reverse:
            return {value:key for key, value in expected_dict.iteritems()}
        else:
            return expected_dict
    
    def __str__(self):
        return str(self.to_dict())
    
    def __iter__(self):
        return self._many1_to_many2.iteritems()
        
    def __contains__(self, key):
        return key in self._one1_to_many2
        
    def __getitem__(self, key):
        return self._one1_to_many2[key]
    
class OneToOneMapping(Mapping):
    
    def _check_mapping(self, mapping):
        """
        Extra verification for one-to-one mapping
        """
        elements1, elements2 = super(OneToOneMapping, self)._check_mapping(mapping)
        
        if len(elements1) > 1:
            raise ValueError('Left mapping part (%s) must contain only one element.' % elements1)
            
        if len(elements2) > 1:
            raise ValueError('Right mapping part (%s) must contain only one element.' % elements2)
        
        return elements1, elements2
    
    @classmethod
    def from_dict(cls, mapping, modality1, modality2):
        M = cls(modality1, modality2)
        for key, value in mapping.iteritems():
            if isinstance(key, NoMatch):
                key = None
            if isinstance(value, NoMatch):
                value = None
            M += ([key], [value])
        return M
        
    def to_dict(self, reverse=False):
        if reverse:
            return {right[0]:left[0] for left, right in self}
        else:
            return {left[0]:right[0] for left, right in self}
            
    def __str__(self):
        return str(self.to_dict())
        
    def __getitem__(self, key):
        return self._one1_to_many2[key][0]
    
    