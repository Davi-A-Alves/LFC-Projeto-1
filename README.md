# Motor de Expressões Regulares (LFC – Projeto 1)

Pipeline: **ER → AST → AFN-ε (Thompson) → AFD (subconjuntos) → AFD mínimo (Moore)**, com simuladores de AFN e AFD,
uma API (FastAPI) e um front-end web (React + TypeScript) com construtor visual e animação do autômato.

## Arquivos
- `parser_er.py`  – ER (texto) → AST (descida recursiva)
- `thompson.py`   – AST → AFN com movimentos vazios
- `subset.py`     – fecho-ε, AFN → AFD, minimização
- `simulador.py`  – simulação de AFN e AFD; ambas retornam `(aceito, rastro)`
- `visual.py`     – tabelas de transição e código Graphviz (.dot)
- `main.py`       – linha de comando / modo interativo
- `testes.py`     – testes (inclui comparação exaustiva com `re`)
- `api.py`        – API FastAPI (`POST /compilar`)
- `front-regex/`  – front-end Vite + React + TypeScript

## Linha de comando
    python main.py "(a|b)*abb" abb aabb ab
    python main.py "(ab)*" "" ab --saida figuras    # '' = cadeia vazia
    python main.py                                  # interativo
    python -m unittest testes -v

Operadores: `|` união, concatenação implícita, `*` `+` `?`, parênteses, `\` para escapar.
PNGs/SVGs exigem Graphviz (`dot`) instalado: `brew install graphviz`.

## Aplicação web

Pré-requisitos: Python 3.9+, Node 18+ e Graphviz.

**1. API** (terminal 1, na raiz do projeto):

    pip install -r requirements.txt
    uvicorn api:app --reload --port 8000

Teste rápido: http://localhost:8000/docs

**2. Front-end** (terminal 2):

    cd front-regex
    npm install        # só na primeira vez
    npm run dev

Abra http://localhost:5173. Escolha o autômato (**AFN-ε**, **AFD** ou **AFD mínimo**), monte a ER clicando nos blocos (ou arrastando-os para a barra; clique num bloco
da barra para removê-lo), digite a cadeia e clique em **Compilar & simular**. A animação percorre o
caminho, um passo por segundo; o último estado fica verde (aceita) ou vermelho (rejeita). No AFN-ε,
o conjunto inteiro de estados ativos (já com o fecho-ε) acende a cada passo, e as arestas ε usadas ficam tracejadas.
Trocar o tipo de autômato depois de compilar recompila na hora.

### Contrato da API

`POST /compilar` — corpo `{"er": "a|b", "cadeia": "ab", "automato": "min"}`
(`automato`: `"afn"`, `"afd"` ou `"min"`; padrão `"min"`) →

    { "status": "ok", "automato": "min", "svg": "<svg ...>",
      "caminho": ["D0", "D1", "D2"], "estados": [["D0"], ["D1"], ["D2"]],
      "aceito": false, "num_estados": 3 }

No AFN, `caminho` traz os conjuntos (`"{q0,q2}"`) e `estados` os nós de cada passo (`["q0", "q2"]`).

ER inválida → HTTP 400 com `{"detail": "Erro de sintaxe na ER: ..."}`.
