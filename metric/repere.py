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

# --------------------------------------------------------------------------- #

from identification import IDMatcher
class REPEREIDMatcher(IDMatcher):
    """
    REPERE ID matcher: 
    Two IDs match if: 
    * they are both anonymous, or
    * they are both named and equal.
    
    """
    
    def __init__(self):
        super(REPEREIDMatcher, self).__init__()
    
    def __call__(self, identifier1, identifier2):
        return (self.is_anonymous(identifier1) and \
               self.is_anonymous(identifier2)) \
            or (identifier1 == identifier2 and \
                self.is_named(identifier1) and \
                self.is_named(identifier2))

    def ncorrect(self, identifiers1, identifiers2):
        # Slightly faster than inherited .ncorrect() method
        named1 = self.named_from(identifiers1)
        named2 = self.named_from(identifiers2)
        anonymous1 = self.anonymous_from(identifiers1)
        anonymous2 = self.anonymous_from(identifiers2)
        return len(named1 & named2) + min(len(anonymous1), len(anonymous2))

    # ------------------------------------------------------------ #
    def is_anonymous(self, identifier):
        return identifier[:8] == 'Inconnu_' \
            or identifier[:7] == 'speaker'
    
    def anonymous_from(self, identifiers):
        return set([identifier for identifier in identifiers \
                               if self.is_anonymous(identifier)])
    # ------------------------------------------------------------ #
    def is_named(self, identifier):
        return identifier[:8] != 'Inconnu_' \
           and identifier[:7] != 'speaker'
    
    def named_from(self, identifiers):
        return set([identifier for identifier in identifiers \
                               if self.is_named(identifier)])

# --------------------------------------------------------------------------- #

from base import BaseErrorRate

EGER_TOTAL = 'total'

EGER_REF_NAME = 'total named in reference'
EGER_REF_ANON = 'total anonymous in reference'
EGER_HYP_NAME = 'total named in hypothesis'
EGER_HYP_ANON = 'total anonymous in hypothesis'
    
EGER_CORRECT_NAME = 'correct named'
EGER_CORRECT_ANON = 'correct anonymous'

EGER_CONFUSION_NAME_NAME = 'confusion named/named'
EGER_CONFUSION_NAME_ANON = 'confusion named/anonymous'
EGER_CONFUSION_ANON_NAME = 'confusion anonymous/named'

EGER_FALSE_ALARM_NAME = 'false alarm named'
EGER_FALSE_ALARM_ANON = 'false alarm anonymous'

EGER_MISS_NAME = 'miss named'
EGER_MISS_ANON = 'miss anonymous'

EGER_NAME = 'estimated global error rate'

class EstimatedGlobalErrorRate(BaseErrorRate):
    """
    Estimated Global Error Rate
    
    Pour chaque image annotée (annotated timeline) de la reference, la liste
    des personnes présentes et/ou parlant à l’instant associé est constituée, 
    et ce du point de vue référence et du point de vue système. 
    
    Ces deux listes sont comparées en associant les personnes une à une, chaque 
    personne ne pouvant être associée au plus qu’une fois. Une association 
    entre deux personnes nommées compte pour un correct, tout comme 
    l’association entre deux anonymes. L’association entre deux personnes avec 
    des noms différents ou entre un nommé et un anonyme donne une confusion. 
    Chaque personne de l’hypothèse non associée compte pour une fausse alarme, 
    et chaque personne de la référence non associée pour un oubli. Un coût est
    associé par confusion, et un par oubli/fausse alarme. 
    
    De toutes les associations possibles est choisie celle qui donne le coût 
    total (erreur pour l’image) le plus faible. 
    La somme de tous ces comptes d’erreur par image permet d’obtenir le nombre 
    d’erreurs global. Le nombre global d’entrées attendues est lui aussi 
    comptabilisé en cumulant le nombre de personnes présentes dans la référence 
    à chaque image. Le taux d’erreur est alors le nombre d’erreurs global 
    divisé par le nombre global d’entrées attendues.
    
    Nous nous proposons d’utiliser un coût de 1 pour oubli/fausse alarme et de 
    0,5 pour confusion.
    
    Example
    
    >>> xgtf = XGTFParser(path2xgtf, path2idx)
    >>> reference = xgtf.head()
    >>> annotated = xgtf.annotated()
    >>> hypothesis = my_super_algorithm()
    >>> eger = EstimatedGlobalErrorRate()
    >>> error_rate = eger(reference, hypothesis, annotated)    
    
    """    
    def __init__(self):
        
        numerator = {EGER_CONFUSION_NAME_NAME: 0.5, \
                     EGER_CONFUSION_NAME_ANON: 0.5, \
                     EGER_CONFUSION_ANON_NAME: 0.5, \
                     EGER_FALSE_ALARM_NAME: 1., \
                     EGER_FALSE_ALARM_ANON: 1., \
                     EGER_MISS_NAME: 1., \
                     EGER_MISS_ANON: 1., }
                     
        denominator = {EGER_REF_NAME: 1., \
                       EGER_REF_ANON: 1., }
        
        other = [EGER_TOTAL, EGER_HYP_NAME, EGER_HYP_ANON, \
                 EGER_CORRECT_NAME, EGER_CORRECT_ANON]
        
        super(EstimatedGlobalErrorRate, self).__init__(EGER_NAME, \
                                                       numerator, \
                                                       denominator, \
                                                       other)
        
        self.matcher = REPEREIDMatcher()
        
    def __call__(self, reference, hypothesis, annotated, detailed=False):
        
        detail = self.initialize()

        reference = reference >> annotated
        hypothesis = hypothesis >> annotated
        
        for frame in annotated:

            ref = reference.ids(frame)
            hyp = hypothesis.ids(frame)
        
            detail[EGER_TOTAL] += len(ref)
        
            name_ref = self.matcher.named_from(ref)
            name_hyp = self.matcher.named_from(hyp)
            detail[EGER_REF_NAME] += len(name_ref)
            detail[EGER_HYP_NAME] += len(name_hyp)
        
            anon_ref = ref - name_ref
            anon_hyp = hyp - name_hyp
            detail[EGER_REF_ANON] += len(anon_ref)
            detail[EGER_HYP_ANON] += len(anon_hyp)

            # correct named/named matches
            detail[EGER_CORRECT_NAME] += len(name_ref & name_hyp)
            for known in name_ref & name_hyp:
                name_ref.remove(known)
                name_hyp.remove(known)
        
            # correct anonymous/anonymous matches
            n = min(len(anon_ref), len(anon_hyp))
            detail[EGER_CORRECT_ANON] += n
            for i in range(n):
                anon_ref.pop()
                anon_hyp.pop()
        
            # named/named confusion
            n = min(len(name_ref), len(name_hyp))
            detail[EGER_CONFUSION_NAME_NAME] += n
            for i in range(n):
                name_ref.pop()
                name_hyp.pop()

            # named/anonymous confusion
            n = min(len(name_ref), len(anon_hyp))
            detail[EGER_CONFUSION_NAME_ANON] += n
            for i in range(n):
                name_ref.pop()
                anon_hyp.pop()
        
            # anonymous/named confusion
            n = min(len(anon_ref), len(name_hyp))
            detail[EGER_CONFUSION_ANON_NAME] += n
            for i in range(n):
                anon_ref.pop()
                name_hyp.pop()
        
            # miss
            detail[EGER_MISS_NAME] += len(name_ref)
            detail[EGER_MISS_ANON] += len(anon_ref)
        
            # false alarm
            detail[EGER_FALSE_ALARM_NAME] += len(name_hyp)
            detail[EGER_FALSE_ALARM_ANON] += len(anon_hyp)
        
        return self.compute(detail, accumulate=True, detailed=detailed)

    def pretty(self, detail):
        
        string = ""
        
        ref_name = detail[EGER_REF_NAME]
        ref_anon  = detail[EGER_REF_ANON]
        string += "  - reference entries: %d (%d named, %d anonymous)\n" % \
                  (ref_name+ref_anon, ref_name, ref_anon)
    
        hyp_name = detail[EGER_HYP_NAME]
        hyp_anon  = detail[EGER_HYP_ANON]
        string += "  - hypothesis entries: %d (%d named, %d anonymous)\n" % \
                  (hyp_name+hyp_anon, hyp_name, hyp_anon)
    
        correct_name = detail[EGER_CORRECT_NAME]
        correct_anon  = detail[EGER_CORRECT_ANON]
        string += "  - correct: %d (%d named, %d anonymous)\n" % \
                  (correct_name+correct_anon, correct_name, correct_anon)
    
        confusion_nn = detail[EGER_CONFUSION_NAME_NAME]
        confusion_na = detail[EGER_CONFUSION_NAME_ANON]
        confusion_an = detail[EGER_CONFUSION_ANON_NAME]
        string += "  - confusions: %d (%d n-n, %d n-a, %d a-n)\n" % \
                  (confusion_nn+confusion_na+confusion_an, \
                   confusion_nn, confusion_na, confusion_an)
        
        miss_name = detail[EGER_MISS_NAME]
        miss_anon = detail[EGER_MISS_ANON]        
        string += "  - miss: %d (%d named, %d anonymous)\n" % \
                  (miss_name+miss_anon, miss_name, miss_anon)
        
        fa_name = detail[EGER_FALSE_ALARM_NAME]
        fa_anon = detail[EGER_FALSE_ALARM_ANON]        
        string += "  - fa: %d (%d named, %d anonymous)\n" % \
                  (fa_name+fa_anon, fa_name, fa_anon)
        
        if detail[EGER_HYP_NAME] > 0:
            precision = 1. * detail[EGER_CORRECT_NAME] / detail[EGER_HYP_NAME]
        else:
            precision = 1.
        string += "  - precision (named): %.2f %%\n" % (100*precision)

        if detail[EGER_HYP_NAME] > 0:
            recall = 1. * detail[EGER_CORRECT_NAME] / detail[EGER_REF_NAME]
        else:
            recall = 1.
        string += "  - recall (named): %.2f %%\n" % (100*recall)
        
        fmeasure = 2 * precision * recall / (precision + recall) 
        string += "  - F1-measure (named): %.2f %%\n" % (100*fmeasure)
        
        string += "  - EGER: %.2f %%\n" % (100*detail[self.name])
        
        return string

# --------------------------------------------------------------------------- #

def main(argv=None):

    import getopt
    import os
    import pyannote.parser
    
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], \
                            "hR:H:F:", \
                            ["help", "reference=", "hypothesis=", \
                             "frames=", "speaker", "head"])
        except getopt.error, msg:
            raise Usage(msg)
        
        path2reference = None
        path2hypothesis = None
        path2frames = None
        speaker = False
        head = False
        for option, value in opts:
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-R", "--reference"):
                path2reference = value
            if option in ("-H", "--hypothesis"):
                path2hypothesis = value
            if option in ("-F", "--frames"):
                path2frames = value
            if option in ("--speaker"):
                speaker = True
            if option in ("--head"):
                head = True
       
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

    reference = pyannote.parser.repere.REPEREParser(path2reference, \
                                                    confidence=False, \
                                                    multitrack=True)
    hypothesis = pyannote.parser.repere.REPEREParser(path2hypothesis, \
                                                     confidence=False, \
                                                     multitrack=True)
    frames = pyannote.parser.nist.UEMParser(path2frames)
    
    modalities = []
    if speaker: 
        modalities.append('speaker')
    if head:
        modalities.append('head')
    
    error = {modality: EstimatedGlobalErrorRate() for modality in modalities}    
    for video in reference.videos():
        print '* %s' % video
        A = frames.timeline(video) 
        for modality in modalities:
            R = reference.annotation(video, modality)
            H = hypothesis.annotation(video, modality)
            value = error[modality](R, H, A, detailed=False)
            print '  - EGER (%s) = %.3f' % (modality, value)
        print ""
    
    for modality in modalities:
        print "=== %s ===" % modality
        print error[modality]
    
# --------------------------------------------------------------------------- #
    
if  __name__ == '__main__':
    import sys
    sys.exit(main())

# --------------------------------------------------------------------------- #
    

        
