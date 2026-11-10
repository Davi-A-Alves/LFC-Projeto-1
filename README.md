# Motor de Expressões Regulares (LFC – Projeto 1)

Pipeline: **ER → AST → AFN-ε (Thompson) → AFD (subconjuntos) → AFD mínimo (Moore)**, com simuladores de AFN e AFD.

## Arquivos
- `parser_er.py`  – ER (texto) → AST (descida recursiva)
- `thompson.py`   – AST → AFN com movimentos vazios
- `subset.py`     – fecho-ε, AFN → AFD, minimização
- `simulador.py`  – simulação de AFN (conjunto de estados) e AFD
- `visual.py`     – tabelas de transição e arquivos Graphviz
- `main.py`       – linha de comando / modo interativo
- `testes.py`     – testes (inclui comparação exaustiva com `re`)

## Uso
    python main.py "(a|b)*abb" abb aabb ab
    python main.py "(ab)*" "" ab --saida figuras    # '' = cadeia vazia
    python main.py                                  # interativo
    python -m unittest testes -v

Operadores: `|` união, concatenação implícita, `*` `+` `?`, parênteses, `\` para escapar.
PNGs exigem Graphviz (`dot`) instalado; sem ele, gera apenas `.dot`.
