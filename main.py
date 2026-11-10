import argparse
import os

from parser_er import parse, ast_para_texto, ErroSintaxe
from thompson import ast_para_afn
from subset import afn_para_afd, minimizar
from simulador import simular_afn, simular_afd
import visual


def processar(er, cadeias, saida=None):
    ast = parse(er)
    afn = ast_para_afn(ast)
    afd = afn_para_afd(afn)
    minimo = minimizar(afd)

    print(f"\nER: {er!r}")
    print(f"AST: {ast_para_texto(ast)}\n")
    print(visual.tabela_afn(afn), "\n")
    print(visual.tabela_afd(afd, "AFD (subconjuntos)"), "\n")
    print(visual.tabela_afd(minimo, "AFD mínimo"), "\n")

    if saida:
        os.makedirs(saida, exist_ok=True)
        for nome, aut in (("afn", afn), ("afd", afd), ("afd_minimo", minimo)):
            print("salvo:", visual.salvar(aut, os.path.join(saida, nome)))
        print()

    if cadeias:
        print(f"{'cadeia':<15}{'AFN':<10}{'AFD':<10}{'AFD mín.':<10}")
        for c in cadeias:
            r = (simular_afn(afn, c), simular_afd(afd, c), simular_afd(minimo, c))
            texto = c if c else "ε"
            print(f"{texto:<15}" + "".join(f"{'aceita' if x else 'rejeita':<10}" for x in r))
            assert len(set(r)) == 1, "simuladores discordam!"


def interativo():
    print("Motor de ER (Ctrl+C para sair). Operadores: | * + ? ( ) e \\ para escapar.")
    while True:
        try:
            er = input("\nER> ")
            cadeias = input("cadeias (separadas por espaço; use '' para vazia)> ").split()
            cadeias = ["" if c == "''" else c for c in cadeias]
            processar(er, cadeias)
        except ErroSintaxe as e:
            print("Erro de sintaxe:", e)
        except (KeyboardInterrupt, EOFError):
            print()
            break


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("er", nargs="?", help="expressão regular")
    ap.add_argument("cadeias", nargs="*", help="cadeias a testar")
    ap.add_argument("--saida", help="pasta para salvar .dot/.png dos autômatos")
    args = ap.parse_args()
    if args.er is None:
        interativo()
    else:
        try:
            processar(args.er, args.cadeias, args.saida)
        except ErroSintaxe as e:
            print("Erro de sintaxe:", e)
