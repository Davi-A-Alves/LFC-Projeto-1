"""Construção de Thompson: AST -> AFN com movimentos vazios (ε)."""
from collections import defaultdict

EPS = "ε"


class AFN:
    """AFN-ε. transicoes[estado][simbolo] = conjunto de estados."""

    def __init__(self):
        self.transicoes = defaultdict(lambda: defaultdict(set))
        self.num_estados = 0
        self.inicial = None
        self.final = None  # a construção de Thompson gera um único final

    def novo_estado(self):
        q = self.num_estados
        self.num_estados += 1
        return q

    def adicionar(self, origem, simbolo, destino):
        self.transicoes[origem][simbolo].add(destino)

    @property
    def estados(self):
        return set(range(self.num_estados))

    @property
    def alfabeto(self):
        simbolos = set()
        for por_simbolo in self.transicoes.values():
            simbolos.update(por_simbolo.keys())
        simbolos.discard(EPS)
        return sorted(simbolos)

    def destinos(self, estado, simbolo):
        return self.transicoes.get(estado, {}).get(simbolo, set())


def _construir(ast, afn):
    """Devolve (estado_inicial, estado_final) do fragmento da AST."""
    tipo = ast[0]

    if tipo == 'sym':
        i, f = afn.novo_estado(), afn.novo_estado()
        afn.adicionar(i, ast[1], f)
        return i, f

    if tipo == 'eps':
        i, f = afn.novo_estado(), afn.novo_estado()
        afn.adicionar(i, EPS, f)
        return i, f

    if tipo == 'cat':
        i1, f1 = _construir(ast[1], afn)
        i2, f2 = _construir(ast[2], afn)
        afn.adicionar(f1, EPS, i2)
        return i1, f2

    if tipo == 'alt':
        i, f = afn.novo_estado(), afn.novo_estado()
        i1, f1 = _construir(ast[1], afn)
        i2, f2 = _construir(ast[2], afn)
        afn.adicionar(i, EPS, i1)
        afn.adicionar(i, EPS, i2)
        afn.adicionar(f1, EPS, f)
        afn.adicionar(f2, EPS, f)
        return i, f

    if tipo in ('star', 'plus', 'opt'):
        i, f = afn.novo_estado(), afn.novo_estado()
        a, b = _construir(ast[1], afn)
        afn.adicionar(i, EPS, a)
        afn.adicionar(b, EPS, f)
        if tipo in ('star', 'plus'):
            afn.adicionar(b, EPS, a)      # repetir
        if tipo in ('star', 'opt'):
            afn.adicionar(i, EPS, f)      # pular (aceita ε)
        return i, f

    raise ValueError(f"nó desconhecido na AST: {tipo}")


def ast_para_afn(ast):
    afn = AFN()
    afn.inicial, afn.final = _construir(ast, afn)
    return afn
