"""API FastAPI que envelopa o Motor de Expressões Regulares.

Uso (na raiz do projeto):
    pip install -r requirements.txt
    uvicorn api:app --reload --port 8000

Documentação interativa: http://localhost:8000/docs
"""
import shutil
import subprocess
from typing import List, Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from parser_er import parse, ErroSintaxe
from thompson import ast_para_afn
from subset import afn_para_afd, minimizar
from simulador import simular_afn, simular_afd
from visual import para_dot


app = FastAPI(title="Motor de Regex API")

# CORS liberado para qualquer porta de localhost / 127.0.0.1 (o Vite usa 5173).
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_methods=["*"],
    allow_headers=["*"],
)


class CompilarRequest(BaseModel):
    er: str = Field(..., max_length=200, examples=["a|b"])
    cadeia: str = Field("", max_length=500, examples=["ab"])
    # "afn" = AFN-ε (Thompson) | "afd" = AFD (subconjuntos) | "min" = AFD mínimo
    automato: Literal["afn", "afd", "min"] = "min"


class CompilarResponse(BaseModel):
    status: str
    automato: str
    svg: str
    caminho: List[str]          # rótulo de cada passo: "D1" (AFD) ou "{q0,q2}" (AFN)
    estados: List[List[str]]    # nós do SVG ativos em cada passo: ["D1"] ou ["q0", "q2"]
    aceito: bool
    num_estados: int


def _dot_para_svg(dot_source: str) -> str:
    """Converte código .dot em SVG usando o Graphviz instalado no sistema."""
    if not shutil.which("dot"):
        raise HTTPException(
            status_code=500,
            detail="Graphviz (dot) não encontrado no PATH. Instale com: brew install graphviz",
        )
    try:
        result = subprocess.run(
            ["dot", "-Tsvg"],
            input=dot_source,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Graphviz demorou demais para gerar o SVG.")
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar SVG: {result.stderr}")
    # Remove o cabeçalho <?xml ...?> e o <!DOCTYPE>, para injetar direto no DOM.
    svg = result.stdout
    inicio = svg.find("<svg")
    return svg[inicio:] if inicio != -1 else svg


@app.post("/compilar", response_model=CompilarResponse)
def compilar(req: CompilarRequest):
    """Compila a ER no autômato escolhido (AFN-ε, AFD ou AFD mínimo), simula a cadeia e devolve o SVG + rastro."""
    # 1. ER -> AST -> AFN-ε -> AFD -> AFD mínimo
    try:
        ast = parse(req.er)
    except ErroSintaxe as e:
        raise HTTPException(status_code=400, detail=f"Erro de sintaxe na ER: {e}")

    afn = ast_para_afn(ast)
    if req.automato == "afn":
        automato = afn
    else:
        afd = afn_para_afd(afn)
        automato = afd if req.automato == "afd" else minimizar(afd)

    # 2. .dot do autômato escolhido -> SVG
    svg_string = _dot_para_svg(para_dot(automato, nome=f"automato_{req.automato}"))

    # 3. Simulação, guardando o rastro de estados
    if req.automato == "afn":
        aceito, caminho = simular_afn(afn, req.cadeia)
        # "{q0,q2}" -> ["q0", "q2"]
        estados = [[q for q in passo.strip("{}").split(",") if q] for passo in caminho]
    else:
        aceito, caminho = simular_afd(automato, req.cadeia)
        estados = [[passo] for passo in caminho]

    return CompilarResponse(
        status="ok",
        automato=req.automato,
        svg=svg_string,
        caminho=caminho,
        estados=estados,
        aceito=aceito,
        num_estados=len(automato.estados),
    )


@app.get("/health")
def health():
    return {"status": "ok"}
