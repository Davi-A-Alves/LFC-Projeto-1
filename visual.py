"""Visualização: tabelas de transição em texto e arquivos Graphviz (.dot/.png)."""
import shutil
import subprocess
from thompson import AFN, EPS


def tabela_afn(afn):
    simbolos = afn.alfabeto + [EPS]
    linhas = [f"AFN-ε: {afn.num_estados} estados | inicial = q{afn.inicial} | final = q{afn.final}"]
    larg = 22
    linhas.append("estado".ljust(10) + "".join(s.ljust(larg) for s in simbolos))
    for q in sorted(afn.estados):
        celulas = []
        for s in simbolos:
            d = afn.destinos(q, s)
            celulas.append(("{" + ",".join(f"q{x}" for x in sorted(d)) + "}" if d else "-").ljust(larg))
        marca = ("->" if q == afn.inicial else "  ") + ("*" if q == afn.final else " ")
        linhas.append(f"{marca}q{q}".ljust(10) + "".join(celulas))
    return "\n".join(linhas)


def tabela_afd(afd, titulo="AFD"):
    linhas = [f"{titulo}: {len(afd.estados)} estados | inicial = D{afd.inicial} | "
              f"finais = {{{', '.join(f'D{q}' for q in sorted(afd.finais))}}}"]
    linhas.append("estado".ljust(8) + "".join(s.ljust(8) for s in afd.alfabeto) + "rótulo")
    for q in sorted(afd.estados):
        celulas = []
        for s in afd.alfabeto:
            d = afd.destino(q, s)
            celulas.append((f"D{d}" if d is not None else "-").ljust(8))
        marca = ("->" if q == afd.inicial else "  ") + ("*" if q in afd.finais else " ")
        rot = afd.rotulos.get(q, "")
        if isinstance(rot, frozenset):
            rot = "{" + ",".join(f"q{x}" for x in sorted(rot)) + "}"
        linhas.append(f"{marca}D{q}".ljust(8) + "".join(celulas) + str(rot))
    return "\n".join(linhas)


def para_dot(automato, nome="automato"):
    """Gera o código Graphviz (.dot) de um AFN ou de um AFD."""
    eh_afn = isinstance(automato, AFN)
    prefixo = "q" if eh_afn else "D"
    estados = sorted(automato.estados)
    finais = {automato.final} if eh_afn else automato.finais

    linhas = [f'digraph {nome} {{', '  rankdir=LR;', '  node [shape=circle];',
              '  __inicio [shape=point];',
              f'  __inicio -> {prefixo}{automato.inicial};']
    for q in estados:
        forma = "doublecircle" if q in finais else "circle"
        linhas.append(f'  {prefixo}{q} [shape={forma}];')

    arestas = {}
    for q in estados:
        if eh_afn:
            for s, destinos in automato.transicoes.get(q, {}).items():
                for d in destinos:
                    arestas.setdefault((q, d), []).append(s)
        else:
            for s, d in automato.transicoes[q].items():
                arestas.setdefault((q, d), []).append(s)
    for (o, d), simbolos in sorted(arestas.items()):
        rotulo = ",".join(sorted(simbolos)).replace("\\", "\\\\").replace('"', '\\"')
        linhas.append(f'  {prefixo}{o} -> {prefixo}{d} [label="{rotulo}"];')
    linhas.append('}')
    return "\n".join(linhas)


def salvar(automato, caminho_base):
    """Salva .dot e, se o Graphviz estiver instalado, também o .png."""
    with open(caminho_base + ".dot", "w", encoding="utf-8") as f:
        f.write(para_dot(automato))
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", caminho_base + ".dot", "-o", caminho_base + ".png"], check=False)
        return caminho_base + ".png"
    return caminho_base + ".dot"
