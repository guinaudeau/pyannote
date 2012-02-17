#!/usr/bin/env python
# encoding: utf-8

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
    
    total = 0
    correct_known = 0
    correct_unknown = 0
    confusion = 0
    false_alarm = 0
    miss = 0
    
    for frame in annotated:
        
        ref = reference.ids(frame)
        hyp = hypothesis.ids(frame)
        
        known_ref = set([identifier for identifier in ref if identifier[:8] != 'Inconnu_'])
        known_hyp = set([identifier for identifier in hyp if identifier[:8] != 'Inconnu_'])
        
        unknown_ref = ref - known_ref
        unknown_hyp = hyp - known_hyp

        frame_correct_known = 0
        for known in known_ref & known_hyp:
            frame_correct_known += 1
            known_ref.remove(known)
            known_hyp.remove(known)
        
        frame_correct_unknown = 0
        for i in range(min(len(unknown_ref), len(unknown_hyp))):
            frame_correct_unknown += 1
            unknown_ref.pop()
            unknown_hyp.pop()
        
        left_ref = known_ref | unknown_ref
        left_hyp = known_hyp | unknown_hyp
        
        frame_confusion = 0
        for i in range(min(len(left_ref), len(left_hyp))):
            frame_confusion += 1
            left_ref.pop()
            left_hyp.pop()
        
        frame_total = len(ref)

        frame_false_alarm = len(left_hyp)
        frame_miss = len(left_ref)
        
        total += frame_total
        correct_known += frame_correct_known
        correct_unknown += frame_correct_unknown
        confusion += frame_confusion
        false_alarm += frame_false_alarm
        miss += frame_miss
    
    rate = 1. * (.5 * confusion + false_alarm + miss) / total
    if detailed:
        return {'error rate': rate, 'confusion': confusion, 'miss': miss, 'false alarm': false_alarm, 'total': total, 'correct known': correct_known, 'correct unknown': correct_unknown} 
    else:
        return rate
    
                
        
        
        
        
        
        
        
