"""AFN -> AFD (construção de subconjuntos) e minimização de AFD (Moore)."""
from thompson import EPS


class AFD:
    """AFD. transicoes[estado][simbolo] = estado."""

    def __init__(self, alfabeto):
        self.alfabeto = list(alfabeto)
        self.transicoes = {}
        self.inicial = None
        self.finais = set()
        self.rotulos = {}  # estado -> descrição (ex.: conjunto de estados do AFN)

    @property
    def estados(self):
        return set(self.transicoes.keys())

    def destino(self, estado, simbolo):
        return self.transicoes.get(estado, {}).get(simbolo)


def fecho_epsilon(afn, conjunto):
    """Estados alcançáveis a partir de 'conjunto' usando só movimentos ε."""
    resultado = set(conjunto)
    pilha = list(conjunto)
    while pilha:
        q = pilha.pop()
        for r in afn.destinos(q, EPS):
            if r not in resultado:
                resultado.add(r)
                pilha.append(r)
    return frozenset(resultado)


def mover(afn, conjunto, simbolo):
    resultado = set()
    for q in conjunto:
        resultado |= afn.destinos(q, simbolo)
    return resultado


def afn_para_afd(afn):
    """Construção de subconjuntos. Cada estado do AFD é um conjunto de estados do AFN."""
    afd = AFD(afn.alfabeto)
    inicial = fecho_epsilon(afn, {afn.inicial})
    ids = {inicial: 0}
    fila = [inicial]
    afd.inicial = 0
    afd.rotulos[0] = inicial

    while fila:
        atual = fila.pop(0)
        id_atual = ids[atual]
        afd.transicoes[id_atual] = {}
        if afn.final in atual:
            afd.finais.add(id_atual)
        for s in afd.alfabeto:
            destino = fecho_epsilon(afn, mover(afn, atual, s))
            if not destino:
                continue  # sem transição = estado de erro implícito
            if destino not in ids:
                ids[destino] = len(ids)
                afd.rotulos[ids[destino]] = destino
                fila.append(destino)
            afd.transicoes[id_atual][s] = ids[destino]
    return afd


def completar(afd):
    """Devolve um AFD completo (acrescenta estado 'morto' se necessário)."""
    novo = AFD(afd.alfabeto)
    novo.inicial = afd.inicial
    novo.finais = set(afd.finais)
    novo.rotulos = dict(afd.rotulos)
    novo.transicoes = {q: dict(t) for q, t in afd.transicoes.items()}
    faltando = any(s not in t for t in novo.transicoes.values() for s in novo.alfabeto)
    if faltando:
        morto = max(novo.transicoes) + 1
        novo.transicoes[morto] = {}
        novo.rotulos[morto] = "∅ (morto)"
        for t in novo.transicoes.values():
            for s in novo.alfabeto:
                t.setdefault(s, morto)
    return novo


def minimizar(afd):
    """Minimização por refinamento de partições (algoritmo de Moore)."""
    afd = completar(afd)
    grupo = {q: (1 if q in afd.finais else 0) for q in afd.transicoes}
    num_grupos = len(set(grupo.values()))

    while True:
        assinaturas = {}
        novo_grupo = {}
        for q in sorted(afd.transicoes):
            ass = (grupo[q], tuple(grupo[afd.transicoes[q][s]] for s in afd.alfabeto))
            novo_grupo[q] = assinaturas.setdefault(ass, len(assinaturas))
        grupo = novo_grupo
        if len(assinaturas) == num_grupos:
            break
        num_grupos = len(assinaturas)

    minimo = AFD(afd.alfabeto)
    minimo.inicial = grupo[afd.inicial]
    for q, t in afd.transicoes.items():
        g = grupo[q]
        minimo.transicoes.setdefault(g, {s: grupo[t[s]] for s in afd.alfabeto})
        minimo.rotulos.setdefault(g, set())
        minimo.rotulos[g].add(q)
        if q in afd.finais:
            minimo.finais.add(g)
    minimo.rotulos = {g: "{" + ",".join(f"D{q}" for q in sorted(qs)) + "}"
                      for g, qs in minimo.rotulos.items()}
    return minimo
