import { useState, useRef, useEffect, useLayoutEffect } from 'react';
import type { DragEvent } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://localhost:8000';
const INTERVALO_MS = 1000;

const LETRAS = 'abcdefghijklmnopqrstuvwxyz'.split('');
const DIGITOS = '0123456789'.split('');
const OPERADORES = ['|', '*', '+', '?', '(', ')'];
const DESCRICAO_OP: Record<string, string> = {
  '|': 'União (ou)',
  '*': 'Fecho de Kleene (0 ou mais)',
  '+': 'Fecho positivo (1 ou mais)',
  '?': 'Opcional (0 ou 1)',
  '(': 'Abre grupo',
  ')': 'Fecha grupo',
};

// Cores da animação
const COR = {
  linha: '#94a3b8',
  texto: '#e2e8f0',
  rotulo: '#8ab4f8',
  visitadoFill: '#1e3a5f',
  visitadoStroke: '#3b82f6',
  atualFill: '#ff00c8',
  atualStroke: '#ffd400',
  aceitoFill: '#00c853',
  rejeitadoFill: '#ff1744',
  arestaAtiva: '#ffd400',
  arestaEps: '#ff6ee0',
};

type Automato = 'afn' | 'afd' | 'min';

const AUTOMATOS: { id: Automato; nome: string; titulo: string; dica: string }[] = [
  {
    id: 'afn',
    nome: 'AFN-ε',
    titulo: 'AFN-ε (Thompson)',
    dica: 'Vários estados ficam ativos ao mesmo tempo: o conjunto atual já inclui o fecho-ε. Arestas ε usadas no passo ficam tracejadas.',
  },
  {
    id: 'afd',
    nome: 'AFD',
    titulo: 'AFD (construção de subconjuntos)',
    dica: 'Cada estado Dn corresponde a um conjunto de estados do AFN. Sem transição = estado de erro implícito.',
  },
  {
    id: 'min',
    nome: 'AFD mínimo',
    titulo: 'AFD mínimo (Moore)',
    dica: 'Menor AFD completo equivalente; pode incluir um estado morto.',
  },
];

interface CompileResult {
  status: string;
  automato: Automato;
  svg: string;
  caminho: string[];
  estados: string[][];
  aceito: boolean;
  num_estados: number;
}

interface Simulacao extends CompileResult {
  cadeia: string; // cadeia que foi enviada (o input pode mudar depois)
}

const MIME_TOKEN = 'text/x-regex-token';

/* ---------- utilitários de manipulação do SVG ---------- */

function pintarNo(no: Element, fill: string, stroke: string, texto: string, largura = '1') {
  no.querySelectorAll('ellipse, polygon').forEach((el) => {
    const s = (el as SVGElement).style;
    s.fill = fill;
    s.stroke = stroke;
    s.strokeWidth = largura;
  });
  no.querySelectorAll('text').forEach((t) => {
    (t as SVGTextElement).style.fill = texto;
  });
}

function pintarAresta(aresta: Element, cor: string, largura: string) {
  aresta.querySelectorAll('path').forEach((p) => {
    const s = (p as SVGElement).style;
    s.stroke = cor;
    s.strokeWidth = largura;
  });
  aresta.querySelectorAll('polygon').forEach((p) => {
    const s = (p as SVGElement).style;
    s.stroke = cor;
    s.fill = cor;
  });
}

function tituloDe(el: Element) {
  return el.querySelector('title')?.textContent?.trim() ?? '';
}

/* ---------- componente ---------- */

function App() {
  const [regex, setRegex] = useState('');
  const [cadeia, setCadeia] = useState('');
  const [automato, setAutomato] = useState<Automato>('min');
  const [result, setResult] = useState<Simulacao | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [passo, setPasso] = useState(-1);
  const [rodada, setRodada] = useState(0); // incrementa para reiniciar a animação
  const [arrastandoSobre, setArrastandoSobre] = useState(false);
  const svgContainerRef = useRef<HTMLDivElement>(null);

  const animando = !!result && passo >= 0 && passo < result.caminho.length - 1;
  const terminou = !!result && passo === result.caminho.length - 1;
  // O rastro fica mais curto que a cadeia quando a leitura trava (sem transição).
  const travou = !!result && result.caminho.length < result.cadeia.length + 1;

  /* ----- construtor ----- */

  const inserir = (token: string, posicao?: number) => {
    setRegex((prev) => {
      const i = posicao ?? prev.length;
      return prev.slice(0, i) + token + prev.slice(i);
    });
  };

  const removerEm = (i: number) => setRegex((prev) => prev.slice(0, i) + prev.slice(i + 1));
  const backspace = () => setRegex((prev) => prev.slice(0, -1));

  const limpar = () => {
    setRegex('');
    setResult(null);
    setError('');
    setPasso(-1);
  };

  const onDragStart = (e: DragEvent, token: string) => {
    e.dataTransfer.setData(MIME_TOKEN, token);
    e.dataTransfer.setData('text/plain', token);
    e.dataTransfer.effectAllowed = 'copy';
  };

  const onDrop = (e: DragEvent, posicao?: number) => {
    e.preventDefault();
    e.stopPropagation();
    setArrastandoSobre(false);
    const token = e.dataTransfer.getData(MIME_TOKEN) || e.dataTransfer.getData('text/plain');
    if (token && token.length === 1) inserir(token, posicao);
  };

  /* ----- submissão ----- */

  const handleSubmit = async (tipo: Automato = automato) => {
    if (!regex) {
      setError('Monte uma expressão regular antes de compilar.');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const resp = await axios.post<CompileResult>(`${API_URL}/compilar`, {
        er: regex,
        cadeia,
        automato: tipo,
      });
      setResult({ ...resp.data, cadeia });
      setRodada((r) => r + 1);
    } catch (err: unknown) {
      setResult(null);
      setPasso(-1);
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        const d = err.response.data.detail;
        setError(typeof d === 'string' ? d : JSON.stringify(d));
      } else {
        setError('Não foi possível falar com a API. Ela está rodando em http://localhost:8000?');
      }
    } finally {
      setLoading(false);
    }
  };

  /* ----- SVG: ajusta tamanho e tema assim que é injetado ----- */

  useLayoutEffect(() => {
    const svg = svgContainerRef.current?.querySelector('svg');
    if (!svg) return;
    // Tamanho natural do Graphviz (em pt); grafos largos (AFN) rolam na horizontal
    // em vez de encolher até ficarem ilegíveis.
    const larguraPx = (parseFloat(svg.getAttribute('width') ?? '0') || 0) * (4 / 3);
    svg.removeAttribute('width');
    svg.removeAttribute('height');
    svg.style.width = '100%';
    svg.style.minWidth = larguraPx > 1800 ? `${larguraPx * 0.55}px` : '';
    svg.style.maxHeight = '60vh';
    // fundo branco que o Graphviz desenha
    svg.querySelectorAll('g.graph > polygon').forEach((p) => {
      (p as SVGElement).style.fill = 'transparent';
      (p as SVGElement).style.stroke = 'transparent';
    });
    svg.querySelectorAll('g.edge text').forEach((t) => {
      (t as SVGElement).style.fill = COR.rotulo;
    });
  }, [result?.svg]);

  /* ----- Motor de animação: percorre `caminho`, 1 passo por segundo ----- */

  useEffect(() => {
    if (!result || result.caminho.length === 0) return;
    let i = 0;
    setPasso(0);
    const timer = window.setInterval(() => {
      i += 1;
      if (i >= result.caminho.length) {
        window.clearInterval(timer);
        return;
      }
      setPasso(i);
    }, INTERVALO_MS);
    return () => window.clearInterval(timer);
  }, [result, rodada]);

  /* ----- A cada passo, repinta os nós/arestas no DOM do SVG ----- */

  useEffect(() => {
    const container = svgContainerRef.current;
    if (!container || !result) return;

    const passos = result.estados;
    const atuais = new Set(passo >= 0 ? passos[passo] : []);
    const anteriores = new Set(passo > 0 ? passos[passo - 1] : []);
    const visitados = new Set(passos.slice(0, Math.max(passo, 0)).flat());
    const final = passo === passos.length - 1;
    const simbolo = passo > 0 ? result.cadeia[passo - 1] : null;

    container.querySelectorAll('g.node').forEach((no) => {
      const nome = tituloDe(no);
      const ehFinal = no.querySelectorAll('ellipse').length > 1; // doublecircle
      if (nome === '__inicio') {
        pintarNo(no, COR.texto, COR.texto, COR.texto);
      } else if (atuais.has(nome)) {
        let fill = COR.atualFill;
        if (final && !result.aceito) fill = COR.rejeitadoFill;
        else if (final && result.aceito && (ehFinal || atuais.size === 1)) fill = COR.aceitoFill;
        pintarNo(no, fill, COR.atualStroke, '#ffffff', '3');
      } else if (visitados.has(nome)) {
        pintarNo(no, COR.visitadoFill, COR.visitadoStroke, COR.texto, '1.5');
      } else {
        pintarNo(no, 'none', COR.linha, COR.texto);
      }
    });

    // Arestas usadas no passo (o Graphviz nomeia como "D0->D1" / "q0->q2"):
    //  - consumindo o símbolo: origem no conjunto anterior, destino no atual;
    //  - movimentos ε (só AFN): origem e destino no conjunto atual (fecho-ε).
    container.querySelectorAll('g.edge').forEach((aresta) => {
      const [origem, destino] = tituloDe(aresta).split('->');
      const rotulos = (aresta.querySelector('text')?.textContent ?? '').split(',');
      const usadaNoSimbolo =
        simbolo !== null && anteriores.has(origem) && atuais.has(destino) && rotulos.includes(simbolo);
      const usadaNoEps = rotulos.includes('ε') && atuais.has(origem) && atuais.has(destino);
      const inicial = passo >= 0 && origem === '__inicio';
      const linhas = aresta.querySelectorAll('path');
      if (usadaNoSimbolo || (inicial && passo === 0)) {
        pintarAresta(aresta, COR.arestaAtiva, '2.5');
        linhas.forEach((l) => ((l as SVGElement).style.strokeDasharray = ''));
      } else if (usadaNoEps) {
        pintarAresta(aresta, COR.arestaEps, '2');
        linhas.forEach((l) => ((l as SVGElement).style.strokeDasharray = '5 4'));
      } else {
        pintarAresta(aresta, COR.linha, '1');
        linhas.forEach((l) => ((l as SVGElement).style.strokeDasharray = ''));
      }
    });
  }, [passo, result]);

  /* ----- render ----- */

  const charLido = passo > 0 && result ? passo - 1 : -1;

  return (
    <div className="app">
      <header className="header">
        <div className="header-glow" />
        <h1 className="title">Motor de Regex</h1>
        <p className="subtitle">Construtor visual &amp; animador de autômatos</p>
      </header>

      <main className="main-content">
        {/* Construtor */}
        <section className="card builder-card">
          <h2 className="card-title">Construtor de expressão regular</h2>
          <div
            className={`regex-display ${arrastandoSobre ? 'regex-display-drop' : ''}`}
            onDragOver={(e) => {
              e.preventDefault();
              e.dataTransfer.dropEffect = 'copy';
              setArrastandoSobre(true);
            }}
            onDragLeave={() => setArrastandoSobre(false)}
            onDrop={(e) => onDrop(e)}
          >
            <div className="regex-text">
              {regex ? (
                regex.split('').map((c, i) => (
                  <button
                    key={i}
                    className={`token ${OPERADORES.includes(c) ? 'token-op' : ''}`}
                    title="Clique para remover · solte um bloco aqui para inserir antes"
                    onClick={() => removerEm(i)}
                    onDragOver={(e) => e.preventDefault()}
                    onDrop={(e) => onDrop(e, i)}
                  >
                    {c}
                  </button>
                ))
              ) : (
                <span className="placeholder">Clique nos blocos abaixo ou arraste-os para cá…</span>
              )}
            </div>
            <div className="regex-actions">
              <button className="btn-icon" onClick={backspace} title="Apagar último">
                ⌫
              </button>
              <button className="btn-icon btn-clear" onClick={limpar} title="Limpar tudo">
                ✕
              </button>
            </div>
          </div>

          <div className="btn-group">
            <h3 className="btn-group-label">Letras</h3>
            <div className="btn-grid">
              {LETRAS.map((c) => (
                <button
                  key={c}
                  className="btn btn-char"
                  draggable
                  onDragStart={(e) => onDragStart(e, c)}
                  onClick={() => inserir(c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="btn-group">
            <h3 className="btn-group-label">Dígitos</h3>
            <div className="btn-grid">
              {DIGITOS.map((c) => (
                <button
                  key={c}
                  className="btn btn-char"
                  draggable
                  onDragStart={(e) => onDragStart(e, c)}
                  onClick={() => inserir(c)}
                >
                  {c}
                </button>
              ))}
            </div>
          </div>

          <div className="btn-group">
            <h3 className="btn-group-label">Operadores</h3>
            <div className="btn-grid btn-grid-ops">
              {OPERADORES.map((op) => (
                <button
                  key={op}
                  className="btn btn-op"
                  title={DESCRICAO_OP[op]}
                  draggable
                  onDragStart={(e) => onDragStart(e, op)}
                  onClick={() => inserir(op)}
                >
                  {op}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Cadeia de teste */}
        <section className="card test-card">
          <h2 className="card-title">Autômato</h2>
          <div className="seletor" role="radiogroup" aria-label="Tipo de autômato">
            {AUTOMATOS.map((a) => (
              <button
                key={a.id}
                role="radio"
                aria-checked={automato === a.id}
                className={`seletor-opcao ${automato === a.id ? 'seletor-opcao-ativa' : ''}`}
                onClick={() => {
                  setAutomato(a.id);
                  if (result && regex) handleSubmit(a.id); // recompila na hora
                }}
              >
                {a.nome}
              </button>
            ))}
          </div>
          <p className="seletor-dica">{AUTOMATOS.find((a) => a.id === automato)!.dica}</p>

          <h2 className="card-title">Cadeia de teste</h2>
          <div className="test-input-row">
            <input
              type="text"
              className="input-field"
              value={cadeia}
              onChange={(e) => setCadeia(e.target.value)}
              placeholder="Digite a cadeia (vazia = ε)"
              onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
            />
            <button className="btn btn-submit" onClick={() => handleSubmit()} disabled={loading}>
              {loading ? <span className="spinner" /> : '▶ Compilar & simular'}
            </button>
          </div>
          {error && <div className="error-msg">{error}</div>}
        </section>

        {/* Resultado */}
        {result && (
          <section className="card result-card">
            <div className="result-header">
              <h2 className="card-title">
                <span className="sem-caixa-alta">
                  {AUTOMATOS.find((a) => a.id === result.automato)!.titulo}
                </span>
                <span className="card-title-extra"> · {result.num_estados} estados</span>
              </h2>
              <div className="result-badges">
                {terminou ? (
                  <span className={`badge ${result.aceito ? 'badge-accept' : 'badge-reject'}`}>
                    {result.aceito ? '✓ Aceita' : '✗ Rejeita'}
                  </span>
                ) : (
                  <span className="badge badge-running">Processando…</span>
                )}
                <button
                  className="btn btn-animate"
                  onClick={() => setRodada((r) => r + 1)}
                  disabled={animando}
                >
                  {animando ? '⏳ Animando…' : '↻ Repetir animação'}
                </button>
              </div>
            </div>

            {/* Fita com a cadeia */}
            <div className="tape">
              <span className="path-label">Fita:</span>
              {result.cadeia.length === 0 ? (
                <span className="tape-cell tape-cell-read">ε</span>
              ) : (
                result.cadeia.split('').map((c, i) => (
                  <span
                    key={i}
                    className={`tape-cell ${i === charLido ? 'tape-cell-active' : ''} ${
                      i < charLido ? 'tape-cell-read' : ''
                    } ${travou && terminou && i === result.caminho.length - 1 ? 'tape-cell-stuck' : ''}`}
                  >
                    {c}
                  </span>
                ))
              )}
            </div>

            <div className="path-display">
              <span className="path-label">Caminho:</span>
              {result.caminho.map((estado, i) => (
                <span
                  key={i}
                  className={`path-state ${i === passo ? 'path-state-active' : ''} ${
                    i < passo ? 'path-state-visited' : ''
                  }`}
                >
                  {estado}
                  {i < result.caminho.length - 1 && (
                    <span className="path-arrow">
                      —{result.cadeia[i]}→
                    </span>
                  )}
                </span>
              ))}
            </div>

            {travou && terminou && (
              <div className="error-msg">
                Não há transição com “{result.cadeia[result.caminho.length - 1]}” a partir de{' '}
                {result.caminho[result.caminho.length - 1]}
                {result.automato === 'afn' ? ' (o conjunto de estados ficou vazio)' : ''}: a leitura
                parou e a cadeia é rejeitada.
              </div>
            )}

            <div
              className="svg-container"
              ref={svgContainerRef}
              dangerouslySetInnerHTML={{ __html: result.svg }}
            />
          </section>
        )}
      </main>

      <footer className="footer">
        <p>Motor de Expressões Regulares — ER → AFN-ε → AFD → AFD mínimo</p>
      </footer>
    </div>
  );
}

export default App;
