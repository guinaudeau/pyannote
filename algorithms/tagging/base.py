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

from pyannote.base.tag import MonoTag

class BaseMonoTagTagger(object):
    
    def __init__(self):
        super(BaseMonoTagTagger, self).__init__()
    
    def tag(self, source, target):
        raise NotImplementedError('')
    
    def __call__(self, source, target):
        
        # make sure both source and target are MonoTag
        if not isinstance(source, MonoTag):
            raise TypeError('Source must be a MonoTag (is %s).' % type(source))
        if not isinstance(target, MonoTag):
            raise TypeError('Target must be a MonoTag (is %s).' % type(target))
        
        # make sure source and target are for the same video
        if source.video != target.video:
            raise ValueError('Video mismatch (%s vs. %s).' \
                             % (source.video, target.video))
        
        return self.tag(source, target)
        # # make MonoTag from Timeline (one label per segment)
        # # and do the actual tagging
        # if isinstance(target, Timeline):
        #     new_target = MonoTag(multitrack=False, \
        #                          video=target.video, \
        #                          modality=source.modality)
        #     for segment in target:
        #         new_target[segment] = Unknown()
        #     return self.tag(source, new_target)
        # # do the actual tagging 
        # else:
        #     return self.tag(source, target)

from pyannote.base.mapping import ManyToOneMapping

class LabelTagger(BaseMonoTagTagger):
    
    def __init__(self):
        super(LabelTagger, self).__init__()
    
    def __get_mapper(self): 
        return self.__mapper
    def __set_mapper(self, mapper): 
        self.__mapper = mapper
    mapper = property(fget=__get_mapper, \
                     fset=__set_mapper, \
                     fdel=None, \
                     doc="Label Mapper.")
    
    def tag(self, source, target):
        # get many-to-one mapping
        mapping = ManyToOneMapping.fromMapping(self.mapper(target, source))
        # translate only mapped labels
        label_func = lambda x: mapping(x) if mapping(x) else x
        return target.copy(label_func=label_func)

from pyannote.base.timeline import Timeline

class BaseTimelineTagger(object):
    def __init__(self):
        super(BaseTimelineTagger, self).__init__()
    
    def tag(self, source, target):
        raise NotImplementedError('')

    def __call__(self, source, target):
        
        # make sure source is MonoTag
        if not isinstance(source, MonoTag):
            raise TypeError('Source must be a MonoTag (is %s).' % type(source))
        # make sure target is Timeline
        if not isinstance(target, Timeline):
            raise TypeError('Target must be a Timeline (is %s).' % type(target))
        
        # make sure source and target are for the same video
        if source.video != target.video:
            raise ValueError('Video mismatch (%s vs. %s).' \
                             % (source.video, target.video))
        
        return self.tag(source, target)
    