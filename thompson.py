EPS = "ε"


class AFN:

    def __init__(self):
        self.transicoes = {}
        self.num_estados = 0
        self.inicial = None
        self.final = None

    def novo_estado(self):
        q = self.num_estados
        self.num_estados += 1
        return q

    def adicionar(self, origem, simbolo, destino):
        if origem not in self.transicoes:
            self.transicoes[origem] = {}
        if simbolo not in self.transicoes[origem]:
            self.transicoes[origem][simbolo] = set()
        self.transicoes[origem][simbolo].add(destino)

    def estados(self):
        return list(range(self.num_estados))

    def alfabeto(self):
        simbolos = set()
        for por_simbolo in self.transicoes.values():
            for simbolo in por_simbolo:
                if simbolo != EPS:
                    simbolos.add(simbolo)
        return sorted(simbolos)

    def destinos(self, estado, simbolo):
        if estado in self.transicoes and simbolo in self.transicoes[estado]:
            return self.transicoes[estado][simbolo]
        return set()


def _construir(ast, afn):
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
            afn.adicionar(b, EPS, a)
        if tipo in ('star', 'opt'):
            afn.adicionar(i, EPS, f)
        return i, f

    raise ValueError(f"nó desconhecido na AST: {tipo}")


def ast_para_afn(ast):
    afn = AFN()
    afn.inicial, afn.final = _construir(ast, afn)
    return afn
