"""Simuladores de AFN (conjunto de estados atuais) e de AFD.

Ambas as funções retornam a tupla (aceito, rastro):
  - aceito: bool com o resultado final;
  - rastro: lista com o estado (ou conjunto de estados) ocupado antes de ler
    o 1º caractere e depois de cada caractere lido. Para uma cadeia de
    tamanho n que é lida até o fim, o rastro tem n + 1 elementos.

Se a leitura travar (nenhuma transição possível), a simulação para ali e o
rastro termina no último estado válido, com aceito = False.
"""
from subset import fecho_epsilon, mover


def _nome_conjunto(conjunto):
    """{0, 3, 1} -> '{q0,q1,q3}'"""
    return "{" + ",".join(f"q{q}" for q in sorted(conjunto)) + "}"


def simular_afn(afn, cadeia):
    """Simula o AFN-ε. Rastro: conjuntos de estados como strings, ex: ['{q0,q2}', '{q1}']."""
    atual = fecho_epsilon(afn, {afn.inicial})
    rastro = [_nome_conjunto(atual)]
    for c in cadeia:
        atual = fecho_epsilon(afn, mover(afn, atual, c))
        if not atual:
            return False, rastro
        rastro.append(_nome_conjunto(atual))
    return afn.final in atual, rastro


def simular_afd(afd, cadeia):
    """Simula o AFD. Rastro: nomes dos estados, ex: ['D0', 'D1', 'D2']."""
    q = afd.inicial
    rastro = [f"D{q}"]
    for c in cadeia:
        q = afd.destino(q, c)
        if q is None:
            return False, rastro
        rastro.append(f"D{q}")
    return q in afd.finais, rastro
