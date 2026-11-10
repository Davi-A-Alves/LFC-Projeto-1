"""Testes: casos esperados + comparação exaustiva com o módulo `re` do Python.

Rodar:  python -m unittest testes -v
"""
import itertools
import re
import unittest

from parser_er import parse, ErroSintaxe
from thompson import ast_para_afn
from subset import afn_para_afd, minimizar
from simulador import simular_afn, simular_afd


def construir(er):
    afn = ast_para_afn(parse(er))
    afd = afn_para_afd(afn)
    return afn, afd, minimizar(afd)


def aceita(er, cadeia):
    afn, afd, minimo = construir(er)
    r_afn, _ = simular_afn(afn, cadeia)
    r_afd, _ = simular_afd(afd, cadeia)
    r_min, _ = simular_afd(minimo, cadeia)
    r = (r_afn, r_afd, r_min)
    assert len(set(r)) == 1, f"simuladores discordam para {er!r} / {cadeia!r}: {r}"
    return r[0]


class TestCasosEsperados(unittest.TestCase):
    CASOS = [
        ("a*b",        ["b", "aab"],               ["", "a", "ba"]),
        ("(a|b)*abb",  ["abb", "aabb", "babb"],    ["", "ab", "abba"]),
        ("a(b|c)*",    ["a", "abcb"],              ["", "b", "ca"]),
        ("(ab)*",      ["", "ab", "abab"],         ["a", "aba", "ba"]),
        ("a+",         ["a", "aaa"],               ["", "b"]),
        ("ab?c",       ["ac", "abc"],              ["abbc", "a"]),
        ("a|b",        ["a", "b"],                 ["", "ab"]),
        ("",           [""],                       ["a"]),
        ("a|",         ["", "a"],                  ["b", "aa"]),
        ("((a|b)c)*",  ["", "ac", "bcac"],         ["a", "cc"]),
        (r"a\*b",      ["a*b"],                    ["ab", "aab"]),
    ]

    def test_casos(self):
        for er, aceitas, rejeitadas in self.CASOS:
            for c in aceitas:
                self.assertTrue(aceita(er, c), f"{er!r} deveria aceitar {c!r}")
            for c in rejeitadas:
                self.assertFalse(aceita(er, c), f"{er!r} deveria rejeitar {c!r}")


class TestContraModuloRe(unittest.TestCase):
    """Compara com re.fullmatch em TODAS as cadeias de {a,b,c} até tamanho 6."""
    ERS = ["a*b", "(a|b)*abb", "a(b|c)*", "(ab)*", "(a|b)*", "a+b?c*",
           "((a|b)(a|c))*", "(a*|b*)c", "(ab|a)(c|bc)?", "a?a?a?aaa", "(a|b|c)+", ""]

    def test_exaustivo(self):
        for er in self.ERS:
            afn, afd, minimo = construir(er)
            padrao = re.compile(er)
            for n in range(0, 7):
                for t in itertools.product("abc", repeat=n):
                    s = "".join(t)
                    esperado = padrao.fullmatch(s) is not None
                    r_afn, _ = simular_afn(afn, s)
                    r_afd, _ = simular_afd(afd, s)
                    r_min, _ = simular_afd(minimo, s)
                    self.assertEqual(r_afn, esperado, f"AFN {er!r} {s!r}")
                    self.assertEqual(r_afd, esperado, f"AFD {er!r} {s!r}")
                    self.assertEqual(r_min, esperado, f"MIN {er!r} {s!r}")


class TestMinimizacao(unittest.TestCase):
    def test_minimo_nao_tem_mais_estados(self):
        for er in ["(a|b)*abb", "(a|a)*", "a*a*a*", "(ab|ab)*"]:
            afn, afd, minimo = construir(er)
            self.assertLessEqual(len(minimo.estados), len(afd.estados) + 1)  # +1: possível estado morto

    def test_afd_minimo_classico(self):
        # (a|b)*abb tem AFD mínimo com 4 estados (completo, sem estado morto)
        _, _, minimo = construir("(a|b)*abb")
        self.assertEqual(len(minimo.estados), 4)


class TestErros(unittest.TestCase):
    def test_erros_de_sintaxe(self):
        for er in ["(a", "a)", "*a", "a|*", "+", "a\\"]:
            with self.assertRaises(ErroSintaxe, msg=er):
                parse(er)


if __name__ == "__main__":
    unittest.main(verbosity=2)
