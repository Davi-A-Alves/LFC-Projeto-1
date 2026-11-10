from thompson import EPS


class AFD:

    def __init__(self, alfabeto):
        self.alfabeto = list(alfabeto)
        self.transicoes = {}
        self.inicial = None
        self.finais = set()
        self.rotulos = {}

    def estados(self):
        return list(self.transicoes.keys())

    def destino(self, estado, simbolo):
        if estado in self.transicoes and simbolo in self.transicoes[estado]:
            return self.transicoes[estado][simbolo]
        return None


def fecho_epsilon(afn, conjunto):
    resultado = set(conjunto)
    pilha = list(conjunto)
    while pilha:
        q = pilha.pop()
        for r in afn.destinos(q, EPS):
            if r not in resultado:
                resultado.add(r)
                pilha.append(r)
    return tuple(sorted(resultado))


def mover(afn, conjunto, simbolo):
    resultado = set()
    for q in conjunto:
        resultado |= afn.destinos(q, simbolo)
    return resultado


def afn_para_afd(afn):
    afd = AFD(afn.alfabeto())
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
                continue
            if destino not in ids:
                ids[destino] = len(ids)
                afd.rotulos[ids[destino]] = destino
                fila.append(destino)
            afd.transicoes[id_atual][s] = ids[destino]
    return afd


def completar(afd):
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
                if s not in t:
                    t[s] = morto
    return novo


def minimizar(afd):
    afd = completar(afd)
    grupo = {q: (1 if q in afd.finais else 0) for q in afd.transicoes}
    num_grupos = len(set(grupo.values()))

    while True:
        assinaturas = {}
        novo_grupo = {}
        for q in sorted(afd.transicoes):
            ass = (grupo[q], tuple(grupo[afd.transicoes[q][s]] for s in afd.alfabeto))
            if ass not in assinaturas:
                assinaturas[ass] = len(assinaturas)
            novo_grupo[q] = assinaturas[ass]
        grupo = novo_grupo
        if len(assinaturas) == num_grupos:
            break
        num_grupos = len(assinaturas)

    minimo = AFD(afd.alfabeto)
    minimo.inicial = grupo[afd.inicial]
    for q, t in afd.transicoes.items():
        g = grupo[q]
        if g not in minimo.transicoes:
            minimo.transicoes[g] = {s: grupo[t[s]] for s in afd.alfabeto}
            minimo.rotulos[g] = []
        minimo.rotulos[g].append(q)
        if q in afd.finais:
            minimo.finais.add(g)
    minimo.rotulos = {g: "{" + ",".join(f"D{q}" for q in sorted(qs)) + "}"
                      for g, qs in minimo.rotulos.items()}
    return minimo
