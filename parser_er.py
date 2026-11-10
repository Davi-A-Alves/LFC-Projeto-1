"""Parser de expressões regulares (descida recursiva).

Gramática (precedência: fecho > concatenação > união):

    uniao  -> concat ( '|' concat )*
    concat -> fecho*                 (vazio = cadeia vazia, ε)
    fecho  -> atomo ( '*' | '+' | '?' )*
    atomo  -> '(' uniao ')' | '\\' CHAR | CHAR

A AST é feita de tuplas:
    ('eps',)  ('sym', c)  ('cat', A, B)  ('alt', A, B)
    ('star', A)  ('plus', A)  ('opt', A)
"""


class ErroSintaxe(Exception):
    pass


class _Parser:
    def __init__(self, texto):
        self.texto = texto
        self.pos = 0

    def olhar(self):
        return self.texto[self.pos] if self.pos < len(self.texto) else None

    def uniao(self):
        esq = self.concat()
        while self.olhar() == '|':
            self.pos += 1
            dir_ = self.concat()
            esq = ('alt', esq, dir_)
        return esq

    def concat(self):
        partes = []
        while self.olhar() not in (None, '|', ')'):
            partes.append(self.fecho())
        if not partes:
            return ('eps',)
        resultado = partes[0]
        for p in partes[1:]:
            resultado = ('cat', resultado, p)
        return resultado

    def fecho(self):
        a = self.atomo()
        nomes = {'*': 'star', '+': 'plus', '?': 'opt'}
        while self.olhar() in nomes:
            a = (nomes[self.olhar()], a)
            self.pos += 1
        return a

    def atomo(self):
        c = self.olhar()
        if c == '(':
            self.pos += 1
            a = self.uniao()
            if self.olhar() != ')':
                raise ErroSintaxe("parêntese '(' não foi fechado")
            self.pos += 1
            return a
        if c == '\\':
            self.pos += 1
            if self.olhar() is None:
                raise ErroSintaxe("'\\' no fim da expressão")
            c = self.olhar()
            self.pos += 1
            return ('sym', c)
        if c in ('*', '+', '?'):
            raise ErroSintaxe(f"operador '{c}' sem operando (posição {self.pos})")
        self.pos += 1
        return ('sym', c)


def parse(texto):
    """Converte a ER (string) em AST."""
    p = _Parser(texto)
    ast = p.uniao()
    if p.pos != len(texto):
        raise ErroSintaxe(f"')' sem '(' correspondente (posição {p.pos})")
    return ast


def ast_para_texto(ast):
    """Representação legível da AST (útil na apresentação)."""
    t = ast[0]
    if t == 'eps':
        return 'ε'
    if t == 'sym':
        return ast[1]
    if t == 'cat':
        return f"({ast_para_texto(ast[1])} · {ast_para_texto(ast[2])})"
    if t == 'alt':
        return f"({ast_para_texto(ast[1])} | {ast_para_texto(ast[2])})"
    return f"{ast_para_texto(ast[1])}{ {'star': '*', 'plus': '+', 'opt': '?'}[t] }"
