#!/usr/bin/env python
# encoding: utf-8

import numpy as np

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

EGER_ERROR_RATE = 'error rate'

def __is_not_anonymous(identifier):
    return identifier[:8] != 'Inconnu_' and identifier[:7] != 'speaker'

def eger(reference, hypothesis, annotated, detailed=False):
    """
    Estimated Global Error Rate
    
    Pour chaque image annotée (annotated timeline) de la reference, la liste des personnes présentes et/ou parlant 
    à l’instant associé est constituée, et ce du point de vue référence et du point de vue système. 
    
    Ces deux listes sont comparées en associant les personnes une à une, chaque personne ne pouvant être associée 
    au plus qu’une fois. Une association entre deux personnes nommées compte pour un correct, tout comme l’association 
    entre deux anonymes. L’association entre deux personnes avec des noms différents ou entre un nommé et un anonyme donne 
    une confusion. Chaque personne de l’hypothèse non associée compte pour une fausse alarme, et chaque personne de la 
    référence non associée pour un oubli. Un coût est associé par confusion, et un par oubli/fausse alarme. 
    
    De toutes les associations possibles est choisie celle qui donne le coût total (erreur pour l’image) le plus faible. 
    La somme de tous ces comptes d’erreur par image permet d’obtenir le nombre d’erreurs global. Le nombre global 
    d’entrées attendues est lui aussi comptabilisé en cumulant le nombre de personnes présentes dans la référence à 
    chaque image. Le taux d’erreur est alors le nombre d’erreurs global divisé par le nombre global d’entrées attendues.
    
    Nous nous proposons d’utiliser un coût de 1 pour oubli/fausse alarme et de 0,5 pour confusion.
    Cette métrique est identique pour la tâche principale et les deux tâches élémentaires, seul l’établissement
    des ensembles de personnes change pour tenir compte uniquement des modalités voulues.    
    
    Example
    
    >>> xgtf = XGTFParser(path2xgtf, path2idx)
    >>> reference = xgtf.head()
    >>> annotated = xgtf.annotated()
    >>> hypothesis = my_super_algorithm()
    >>> error_rate = eger(reference, hypothesis, annotated)    
    
    """
    reference = reference >> annotated
    hypothesis = hypothesis >> annotated
    
    local = {}
    
    for frame in annotated:
        
        local[frame] = {}
        
        ref = reference.ids(frame)
        hyp = hypothesis.ids(frame)
        
        local[frame][EGER_TOTAL] = len(ref)
        
        known_ref = set([identifier for identifier in ref if __is_not_anonymous(identifier)])
        known_hyp = set([identifier for identifier in hyp if __is_not_anonymous(identifier)])
        local[frame][EGER_REF_NAME] = len(known_ref)
        local[frame][EGER_HYP_NAME] = len(known_hyp)
        
        unknown_ref = ref - known_ref
        unknown_hyp = hyp - known_hyp
        local[frame][EGER_REF_ANON] = len(unknown_ref)
        local[frame][EGER_HYP_ANON] = len(unknown_hyp)

        # correct named/named matches
        local[frame][EGER_CORRECT_NAME] = len(known_ref & known_hyp)
        for known in known_ref & known_hyp:
            known_ref.remove(known)
            known_hyp.remove(known)
        
        # correct anonymous/anonymous matches
        n = min(len(unknown_ref), len(unknown_hyp))
        local[frame][EGER_CORRECT_ANON] = n
        for i in range(n):
            unknown_ref.pop()
            unknown_hyp.pop()
        
        # named/named confusion
        n = min(len(known_ref), len(known_hyp))
        local[frame][EGER_CONFUSION_NAME_NAME] = n
        for i in range(n):
            known_ref.pop()
            known_hyp.pop()

        # named/anonymous confusion
        n = min(len(known_ref), len(unknown_hyp))
        local[frame][EGER_CONFUSION_NAME_ANON] = n
        for i in range(n):
            known_ref.pop()
            unknown_hyp.pop()
        
        # anonymous/named confusion
        n = min(len(unknown_ref), len(known_hyp))
        local[frame][EGER_CONFUSION_ANON_NAME] = n
        for i in range(n):
            unknown_ref.pop()
            known_hyp.pop()
        
        # miss
        local[frame][EGER_MISS_NAME] = len(known_ref)
        local[frame][EGER_MISS_ANON] = len(unknown_ref)
        
        # false alarm
        local[frame][EGER_FALSE_ALARM_NAME] = len(known_hyp)
        local[frame][EGER_FALSE_ALARM_ANON] = len(unknown_hyp)
        
    detail = global_eger(local.values(), detailed=detailed)
    
    if detailed:
        return detail
    else:
        return detail[EGER_ERROR_RATE]


def global_eger(local_egers, detailed=False):
    
    detail = { \
        EGER_TOTAL: 0, \
        EGER_REF_NAME: 0, \
        EGER_REF_ANON: 0, \
        EGER_HYP_NAME: 0, \
        EGER_HYP_ANON: 0, \
        EGER_CORRECT_NAME: 0, \
        EGER_CORRECT_ANON: 0, \
        EGER_CONFUSION_NAME_NAME: 0, \
        EGER_CONFUSION_NAME_ANON: 0, \
        EGER_CONFUSION_ANON_NAME: 0, \
        EGER_FALSE_ALARM_NAME: 0, \
        EGER_FALSE_ALARM_ANON: 0, \
        EGER_MISS_NAME: 0, \
        EGER_MISS_ANON: 0, \
        }    
    
    for local in local_egers:
        
        detail[EGER_TOTAL] += local[EGER_TOTAL] 
        detail[EGER_REF_NAME] += local[EGER_REF_NAME]
        detail[EGER_REF_ANON] += local[EGER_REF_ANON]
        detail[EGER_HYP_NAME] += local[EGER_HYP_NAME]
        detail[EGER_HYP_ANON] += local[EGER_HYP_ANON]
        detail[EGER_CORRECT_NAME] += local[EGER_CORRECT_NAME]
        detail[EGER_CORRECT_ANON] += local[EGER_CORRECT_ANON]
        detail[EGER_CONFUSION_NAME_NAME] += local[EGER_CONFUSION_NAME_NAME]
        detail[EGER_CONFUSION_NAME_ANON] += local[EGER_CONFUSION_NAME_ANON]
        detail[EGER_CONFUSION_ANON_NAME] += local[EGER_CONFUSION_ANON_NAME]
        detail[EGER_FALSE_ALARM_NAME] += local[EGER_FALSE_ALARM_NAME]
        detail[EGER_FALSE_ALARM_ANON] += local[EGER_FALSE_ALARM_ANON]
        detail[EGER_MISS_NAME] += local[EGER_MISS_NAME]
        detail[EGER_MISS_ANON] += local[EGER_MISS_ANON]
        
    if detail[EGER_TOTAL] > 0:
        rate = ( \
                    .5 * (detail[EGER_CONFUSION_NAME_NAME] + \
                          detail[EGER_CONFUSION_ANON_NAME] + \
                          detail[EGER_CONFUSION_NAME_ANON]) + \
                    1. * (detail[EGER_FALSE_ALARM_NAME] + \
                          detail[EGER_FALSE_ALARM_ANON]) + \
                    1. * (detail[EGER_MISS_NAME] + \
                          detail[EGER_MISS_ANON]) \
                ) / detail[EGER_TOTAL]
    else:
        rate = 0.
    
    detail[EGER_ERROR_RATE] = rate    
    
    if detailed:
        return detail
    else:
        return rate

def print_eger(detail):
    
    ref_named = detail[EGER_REF_NAME]
    ref_anon  = detail[EGER_REF_ANON]
    print "  - reference entries: %d (%d named, %d anonymous)" % (ref_named+ref_anon, ref_named, ref_anon)

    hyp_named = detail[EGER_HYP_NAME]
    hyp_anon  = detail[EGER_HYP_ANON]
    print "  - hypothesis entries: %d (%d named, %d anonymous)" % (hyp_named+hyp_anon, hyp_named, hyp_anon)

    correct_named = detail[EGER_CORRECT_NAME]
    correct_anon  = detail[EGER_CORRECT_ANON]
    print "  - correct: %d (%d named, %d anonymous)" % (correct_named+correct_anon, correct_named, correct_anon)

    confusion_nn = detail[EGER_CONFUSION_NAME_NAME]
    confusion_na = detail[EGER_CONFUSION_NAME_ANON]
    confusion_an = detail[EGER_CONFUSION_ANON_NAME]
    print "  - confusions: %d (%d n-n, %d n-a, %d a-n)" % (confusion_nn+confusion_na+confusion_an, confusion_nn, confusion_na, confusion_an)
        
    miss_named = detail[EGER_MISS_NAME]
    miss_anon = detail[EGER_MISS_ANON]        
    print "  - miss: %d (%d named, %d anonymous)" % (miss_named+miss_anon, miss_named, miss_anon)
        
    fa_named = detail[EGER_FALSE_ALARM_NAME]
    fa_anon = detail[EGER_FALSE_ALARM_ANON]        
    print "  - fa: %d (%d named, %d anonymous)" % (fa_named+fa_anon, fa_named, fa_anon)

    if ref_named + ref_anon > 0:
        rate = (.5 * (confusion_nn + confusion_na + confusion_an) + 1. * (miss_named+miss_anon) + 1. * (fa_named+fa_anon)) / (ref_named + ref_anon)
    else:
        rate = 0.
    print "  - EGER: %g %%" % (100*rate)
    print ""


# =================================================================================

def main(argv=None):

    import getopt
    import os
    import pyannote.parser
    import numpy as np
    
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], \
                                       "hR:H:F:", \
                                       ["help", "reference=", "hypothesis=", "frames=", "speaker", "head"])
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

    reference = pyannote.parser.repere.REPEREParser(path2reference, confidence=False, multitrack=True)
    hypothesis = pyannote.parser.repere.REPEREParser(path2hypothesis, confidence=False, multitrack=True)
    frames = pyannote.parser.nist.UEMParser(path2frames)
    
    modalities = []
    if speaker: 
        modalities.append('speaker')
    if head:
        modalities.append('head')
    
    error = {}
    
    reference_entries_named = {modality: 0 for modality in modalities}
    reference_entries_named = {modality: 0 for modality in modalities}
    
    for video in reference.videos():
        error[video] = {}
        print '* %s' % video
        A = frames.timeline(video) 
        for modality in modalities:
            R = reference.annotation(video, modality)
            H = hypothesis.annotation(video, modality)
            error[video][modality] = eger(R, H, A, detailed=True)
            print '  - EGER (%s) = %.3f' % (modality, error[video][modality]['error rate'])
        print ""
    
    for modality in modalities:
        print "=== %s ===" % modality
        detail = global_eger([error[video][modality] for video in reference.videos()], detailed=True)
        print_eger(detail)
        
if  __name__ == '__main__':
    import sys
    sys.exit(main())
    

        
