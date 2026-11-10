import shutil
import subprocess

from thompson import EPS


def tabela_afn(afn):
    simbolos = afn.alfabeto() + [EPS]
    linhas = ["AFN-ε (Thompson)", f"inicial: q{afn.inicial}   final: q{afn.final}"]
    linhas.append(f"{'estado':<8}" + "".join(f"{s:<12}" for s in simbolos))
    for q in afn.estados():
        celulas = []
        for s in simbolos:
            destinos = sorted(afn.destinos(q, s))
            if destinos:
                celulas.append("{" + ",".join(f"q{d}" for d in destinos) + "}")
            else:
                celulas.append("-")
        linhas.append(f"q{q:<7}" + "".join(f"{c:<12}" for c in celulas))
    return "\n".join(linhas)


def tabela_afd(afd, titulo="AFD"):
    linhas = [titulo, f"inicial: {afd.inicial}   finais: {sorted(afd.finais)}"]
    linhas.append(f"{'estado':<8}" + "".join(f"{s:<8}" for s in afd.alfabeto) + "rótulo")
    for q in sorted(afd.transicoes):
        celulas = [str(afd.destino(q, s)) if afd.destino(q, s) is not None else "-"
                   for s in afd.alfabeto]
        rotulo = afd.rotulos.get(q, "")
        if isinstance(rotulo, tuple):
            rotulo = "{" + ",".join(f"q{x}" for x in sorted(rotulo)) + "}"
        linhas.append(f"{q:<8}" + "".join(f"{c:<8}" for c in celulas) + str(rotulo))
    return "\n".join(linhas)


def _montar_dot(nomes, inicial, finais, arestas):
    linhas = ["digraph G {", "  rankdir=LR;", "  inicio [shape=point];",
              f'  inicio -> "{nomes[inicial]}";']
    for estado, nome in nomes.items():
        forma = "doublecircle" if estado in finais else "circle"
        linhas.append(f'  "{nome}" [shape={forma}];')
    for origem, simbolo, destino in arestas:
        linhas.append(f'  "{nomes[origem]}" -> "{nomes[destino]}" [label="{simbolo}"];')
    linhas.append("}")
    return "\n".join(linhas)


def dot_afn(afn):
    nomes = {q: f"q{q}" for q in afn.estados()}
    arestas = []
    for origem, por_simbolo in afn.transicoes.items():
        for simbolo, destinos in por_simbolo.items():
            for destino in destinos:
                arestas.append((origem, simbolo, destino))
    return _montar_dot(nomes, afn.inicial, {afn.final}, arestas)


def dot_afd(afd):
    nomes = {q: f"D{q}" for q in afd.transicoes}
    arestas = []
    for origem, por_simbolo in afd.transicoes.items():
        for simbolo, destino in por_simbolo.items():
            arestas.append((origem, simbolo, destino))
    return _montar_dot(nomes, afd.inicial, afd.finais, arestas)


def salvar(automato, caminho):
    texto = dot_afn(automato) if hasattr(automato, "final") else dot_afd(automato)
    with open(caminho + ".dot", "w", encoding="utf-8") as arquivo:
        arquivo.write(texto)
    if shutil.which("dot"):
        subprocess.run(["dot", "-Tpng", caminho + ".dot", "-o", caminho + ".png"], check=True)
        return caminho + ".png"
    return caminho + ".dot"
