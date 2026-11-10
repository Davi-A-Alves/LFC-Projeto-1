from subset import fecho_epsilon, mover


def simular_afn(afn, cadeia):
    atual = fecho_epsilon(afn, {afn.inicial})
    for c in cadeia:
        atual = fecho_epsilon(afn, mover(afn, atual, c))
        if not atual:
            return False
    return afn.final in atual


def simular_afd(afd, cadeia):
    q = afd.inicial
    for c in cadeia:
        q = afd.destino(q, c)
        if q is None:
            return False
    return q in afd.finais
