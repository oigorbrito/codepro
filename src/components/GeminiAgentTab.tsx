import React, { useState, useEffect } from 'react';
import {
  Bot,
  Play,
  ShieldCheck,
  AlertOctagon,
  CheckCircle2,
  XCircle,
  Clock,
  FileCode,
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Copy,
  Check,
  Sliders,
  ShieldAlert,
  Info
} from 'lucide-react';

interface GeminiStatus {
  available: boolean;
  model: string;
  key_configured: boolean;
  rate_limit_policy: {
    tier: string;
    rpm_limit: number;
    rpd_limit: number;
    privacy: string;
  };
  decision_basis: {
    problem_class: string;
    decision: string;
    basis_type: string;
    basis_ref: string;
    supported_claim: string;
    applicability: string;
    deviation: string;
  };
}

interface TelemetryEvent {
  timestamp: string;
  type: string;
  run_id: string;
  data: Record<string, unknown>;
}

interface GeminiRunResult {
  run_id: string;
  status: 'VERIFIED' | 'FAILED' | 'BLOCKED' | 'REJECTED' | 'TIMED_OUT';
  reason: string;
  evidence_root: string;
  changed_files: string[];
  duration_ms: number;
  events: TelemetryEvent[];
  model_response?: {
    summary: string;
    patch: string;
    proposed_files: string[];
    explanation: string;
  };
  replay_audit?: {
    integrity: 'COMPLETE' | 'EMPTY' | 'INVALID' | 'TAMPERED';
    event_count: number;
    head_digest: string | null;
    failures: string[];
  };
  chained_events?: Array<{
    sequence: number;
    event_type: string;
    payload: Record<string, unknown>;
    previous_digest: string | null;
    digest: string;
  }>;
}

interface CharacterizeResult {
  candidate_files: string[];
  affected_components: string[];
  ambiguity_markers: string[];
  risk_markers: string[];
  reasoning: string;
}

export interface CodeProIssue {
  number: number;
  title: string;
  state: string;
  body: string;
  scope: string[];
  candidate_files: string[];
}

interface GeminiAgentTabProps {
  onApplySignalsToP1?: (signals: {
    candidate_files: string[];
    affected_components: string[];
    ambiguity_markers: string[];
    risk_markers: string[];
  }) => void;
}

export function GeminiAgentTab({ onApplySignalsToP1 }: GeminiAgentTabProps) {
  // Status
  const [status, setStatus] = useState<GeminiStatus | null>(null);
  const [loadingStatus, setLoadingStatus] = useState(false);

  // Mode: 'execute' | 'characterize'
  const [activeSubMode, setActiveSubMode] = useState<'execute' | 'characterize'>(() => {
    return (localStorage.getItem('codepro_gemini_submode') as 'execute' | 'characterize') || 'execute';
  });

  // Execution State
  const [requestId, setRequestId] = useState(() => localStorage.getItem('codepro_gemini_req_id') || 'req-gemini-v1');
  const [taskId, setTaskId] = useState(() => localStorage.getItem('codepro_gemini_task_id') || 'task-fix-null-pointer');
  const [prompt, setPrompt] = useState(() => {
    return localStorage.getItem('codepro_gemini_prompt') || 
      'In src/chassis/contracts.ts, add an optional field `telemetry_source` to TelemetryEvent and export a helper validator function isEventValid().';
  });
  const [scope, setScope] = useState(() => {
    return localStorage.getItem('codepro_gemini_scope') || 'src/chassis/contracts.ts\ntests/test_contracts.ts';
  });
  const [candidateFiles, setCandidateFiles] = useState(() => {
    return localStorage.getItem('codepro_gemini_candidate_files') || 'src/chassis/contracts.ts';
  });
  const [selectedModel, setSelectedModel] = useState(() => localStorage.getItem('codepro_gemini_model') || 'gemini-2.5-flash');
  const [isExecuting, setIsExecuting] = useState(false);
  const [runResult, setRunResult] = useState<GeminiRunResult | null>(() => {
    const saved = localStorage.getItem('codepro_gemini_run_result');
    return saved ? JSON.parse(saved) : null;
  });
  const [copiedPatch, setCopiedPatch] = useState(false);

  // Characterization State
  const [issueText, setIssueText] = useState(() => {
    return localStorage.getItem('codepro_gemini_issue_text') || 
      'Users report that when running codepro inspect on a directory without git repo, the git status crashes instead of failing closed gracefully with git_repository=false.';
  });
  const [charLoading, setCharLoading] = useState(false);
  const [charOutput, setCharOutput] = useState<CharacterizeResult | null>(() => {
    const saved = localStorage.getItem('codepro_gemini_char_output');
    return saved ? JSON.parse(saved) : null;
  });
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Issues State
  const [issuesList, setIssuesList] = useState<CodeProIssue[]>([]);
  const [loadingIssues, setLoadingIssues] = useState(false);
  const [selectedIssueNumber, setSelectedIssueNumber] = useState<number | ''>('');
  const [githubToken, setGithubToken] = useState('');
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [issuesSource, setIssuesSource] = useState<string>('codepro_internal_registry');

  // Auto-sync states to localStorage
  useEffect(() => {
    localStorage.setItem('codepro_gemini_submode', activeSubMode);
    localStorage.setItem('codepro_gemini_req_id', requestId);
    localStorage.setItem('codepro_gemini_task_id', taskId);
    localStorage.setItem('codepro_gemini_prompt', prompt);
    localStorage.setItem('codepro_gemini_scope', scope);
    localStorage.setItem('codepro_gemini_candidate_files', candidateFiles);
    localStorage.setItem('codepro_gemini_model', selectedModel);
    localStorage.setItem('codepro_gemini_issue_text', issueText);
    if (runResult) {
      localStorage.setItem('codepro_gemini_run_result', JSON.stringify(runResult));
    } else {
      localStorage.removeItem('codepro_gemini_run_result');
    }
    if (charOutput) {
      localStorage.setItem('codepro_gemini_char_output', JSON.stringify(charOutput));
    } else {
      localStorage.removeItem('codepro_gemini_char_output');
    }
  }, [activeSubMode, requestId, taskId, prompt, scope, candidateFiles, selectedModel, issueText, runResult, charOutput]);

  // Fetch status and issues on load
  const fetchIssues = async (token?: string) => {
    setLoadingIssues(true);
    try {
      const url = token ? `/api/codepro/issues?token=${encodeURIComponent(token)}` : '/api/codepro/issues';
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setIssuesList(data.issues || []);
        setIssuesSource(data.source || 'codepro_internal_registry');
      }
    } catch (err) {
      console.error('Failed to load CodePro issues:', err);
    } finally {
      setLoadingIssues(false);
    }
  };

  const handleSelectIssue = (num: number) => {
    setSelectedIssueNumber(num);
    const found = issuesList.find((i) => i.number === num);
    if (!found) return;

    setTaskId(`codepro-issue-${found.number}`);
    setPrompt(found.body || found.title);
    setScope(found.scope.join('\n'));
    setCandidateFiles(found.candidate_files.join('\n'));
    setIssueText(found.body || found.title);
  };

  // Fetch status on load
  const fetchStatus = async () => {
    setLoadingStatus(true);
    try {
      const res = await fetch('/api/gemini/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to load Gemini status:', err);
    } finally {
      setLoadingStatus(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchIssues();
  }, []);

  const handleExecute = async () => {
    setIsExecuting(true);
    setRunResult(null);
    setErrorMessage(null);

    try {
      const scopeList = scope
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const candidatesList = candidateFiles
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);

      const res = await fetch('/api/gemini/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          request_id: requestId,
          task_id: taskId,
          prompt,
          scope: scopeList,
          candidate_files: candidatesList,
          model: selectedModel,
        }),
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        setErrorMessage(data.error || 'Falha na execução do Gemini');
      } else {
        setRunResult(data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha na conexão';
      setErrorMessage(msg);
      console.error('Gemini execution error:', err);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleCharacterize = async () => {
    setCharLoading(true);
    setCharOutput(null);
    setErrorMessage(null);

    try {
      const res = await fetch('/api/gemini/characterize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ issue: issueText }),
      });

      const data = await res.json();
      if (!res.ok || data.error) {
        setErrorMessage(data.error || 'Falha na caracterização com Gemini');
      } else {
        setCharOutput(data);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha na conexão';
      setErrorMessage(msg);
      console.error('Gemini characterization error:', err);
    } finally {
      setCharLoading(false);
    }
  };

  const copyPatchToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedPatch(true);
    setTimeout(() => setCopiedPatch(false), 2000);
  };

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      {/* Top Header Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-md shadow-indigo-500/20">
              <Bot className="h-6 w-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-tight">Gemini Governed Executor</h2>
                <span className="rounded bg-indigo-950 px-2 py-0.5 font-mono text-xs text-indigo-400 border border-indigo-800">
                  @google/genai SDK
                </span>
                <span className="rounded bg-emerald-950 px-2 py-0.5 font-mono text-xs text-emerald-400 border border-emerald-800">
                  FAIL-CLOSED SCOPE GUARD
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Execução de modelos governada pelo CodePro: escopo estrito, telemetria P0 e sem adulteração fora dos limites autorizados.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="flex items-center space-x-2 rounded-lg bg-slate-950/80 px-3 py-1.5 border border-slate-800">
              <div
                className={`h-2.5 w-2.5 rounded-full ${
                  status?.key_configured ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
                }`}
              />
              <span className="text-xs font-mono text-slate-300">
                {status?.key_configured ? 'API Key Configurada (Server-Side)' : 'Key Ausente (Fail-Closed)'}
              </span>
            </div>

            <button
              onClick={fetchStatus}
              className="flex items-center space-x-1 rounded-lg bg-slate-800 px-3 py-1.5 text-xs text-slate-300 hover:bg-slate-700 hover:text-white transition border border-slate-700"
              title="Recarregar status"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${loadingStatus ? 'animate-spin' : ''}`} />
              <span>Status</span>
            </button>
          </div>
        </div>

        {/* Rate limits and Governance info banner */}
        <div className="mt-4 grid grid-cols-1 md:grid-cols-4 gap-3 border-t border-slate-800/80 pt-4 text-xs font-mono">
          <div className="rounded-lg bg-slate-950/50 p-2.5 border border-slate-800/50">
            <div className="text-slate-400 text-[11px]">Plano & Modelo</div>
            <div className="text-indigo-300 font-semibold mt-0.5">Free Tier • {status?.model || 'gemini-2.5-flash'}</div>
          </div>
          <div className="rounded-lg bg-slate-950/50 p-2.5 border border-slate-800/50">
            <div className="text-slate-400 text-[11px]">Cotas Gratuitas</div>
            <div className="text-slate-200 mt-0.5">15 RPM • 1.500 Requisições/Dia</div>
          </div>
          <div className="rounded-lg bg-slate-950/50 p-2.5 border border-slate-800/50">
            <div className="text-slate-400 text-[11px]">Envelope de Segurança</div>
            <div className="text-emerald-400 mt-0.5">Proxy Server-side (Zero Chave na UI)</div>
          </div>
          <div className="rounded-lg bg-slate-950/50 p-2.5 border border-slate-800/50">
            <div className="text-slate-400 text-[11px]">Decision Basis</div>
            <div className="text-amber-300 mt-0.5">LOCAL_DESIGN_HYPOTHESIS</div>
          </div>
        </div>
      </div>

      {/* Error / Alert notification banner */}
      {errorMessage && (
        <div className="rounded-xl border border-rose-800/80 bg-rose-950/40 p-4 text-xs font-mono text-rose-300 flex items-start space-x-3">
          <AlertOctagon className="h-5 w-5 text-rose-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <div className="font-bold text-rose-200">Falha na Comunicação com Gemini:</div>
            <div>{errorMessage}</div>
            <div className="text-[11px] text-rose-400/80">
              Certifique-se de que a variável GEMINI_API_KEY no ambiente do servidor é uma chave válida emitida pelo Google AI Studio.
            </div>
          </div>
        </div>
      )}

      {/* Sub-modes selector */}
      <div className="flex border-b border-slate-800 space-x-6 text-sm font-medium">
        <button
          onClick={() => setActiveSubMode('execute')}
          className={`pb-3 flex items-center space-x-2 border-b-2 transition ${
            activeSubMode === 'execute'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Play className="h-4 w-4" />
          <span>Execução de Código Governada (P5 Patch)</span>
        </button>
        <button
          onClick={() => setActiveSubMode('characterize')}
          className={`pb-3 flex items-center space-x-2 border-b-2 transition ${
            activeSubMode === 'characterize'
              ? 'border-indigo-500 text-indigo-400'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="h-4 w-4" />
          <span>Caracterizador de Tarefas Assistido (P1 Sinais)</span>
        </button>
      </div>

      {/* CodePro Issues Quick-Selector Bar */}
      <div className="rounded-xl border border-indigo-900/50 bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950/30 p-4 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-ping" />
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Issues deste Repositório (CodePro / oigorbrito/codepro)
              </h3>
              <span className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[10px] text-slate-300 border border-slate-700">
                {issuesSource === 'github_live_api' ? 'Sincronizado com GitHub' : 'Catálogo Arquitetural'}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Selecione uma issue real para carregar automaticamente o escopo autorizado, arquivos candidatos e descrição do problema.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <select
              value={selectedIssueNumber}
              onChange={(e) => {
                const val = e.target.value ? Number(e.target.value) : '';
                if (typeof val === 'number') {
                  handleSelectIssue(val);
                } else {
                  setSelectedIssueNumber('');
                }
              }}
              className="rounded-lg bg-slate-950 px-3 py-2 text-xs font-mono text-indigo-300 border border-indigo-800 focus:border-indigo-500 focus:outline-none min-w-[280px]"
            >
              <option value="">-- Selecionar uma Issue do CodePro --</option>
              {issuesList.map((iss) => (
                <option key={iss.number} value={iss.number}>
                  #{iss.number}: {iss.title}
                </option>
              ))}
            </select>

            <button
              onClick={() => setShowTokenModal(!showTokenModal)}
              className="rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-2 text-xs font-mono text-slate-300 transition border border-slate-700 flex items-center space-x-1 shrink-0"
              title="Configurar GitHub Token para ler issues privadas"
            >
              <span>GitHub Token</span>
            </button>
          </div>
        </div>

        {/* Optional GitHub Token Box */}
        {showTokenModal && (
          <div className="mt-3 pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row items-center gap-2">
            <span className="text-[11px] text-slate-400 shrink-0">
              GitHub PAT (para ler repo privado oigorbrito/codepro):
            </span>
            <input
              type="password"
              placeholder="ghp_xxxx..."
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              className="rounded bg-slate-950 px-2.5 py-1 text-xs font-mono text-slate-200 border border-slate-700 w-full sm:w-72 focus:outline-none focus:border-indigo-500"
            />
            <button
              onClick={() => {
                fetchIssues(githubToken);
                setShowTokenModal(false);
              }}
              disabled={loadingIssues}
              className="rounded bg-indigo-600 hover:bg-indigo-500 px-3 py-1 text-xs text-white font-medium shrink-0 disabled:opacity-50"
            >
              {loadingIssues ? 'Conectando...' : 'Buscar no GitHub'}
            </button>
          </div>
        )}
      </div>

      {/* SUBMODE 1: GOVERNED TASK EXECUTION */}
      {activeSubMode === 'execute' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Left Form: Run Configuration */}
          <div className="lg:col-span-6 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                  <FileCode className="h-4 w-4 text-indigo-400" />
                  <span>Configuração da Execução Governada</span>
                </h3>
                <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                  Chassis Enforcement
                </span>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Request ID</label>
                  <input
                    type="text"
                    value={requestId}
                    onChange={(e) => setRequestId(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 border border-slate-800 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-mono text-slate-400 mb-1">Task ID</label>
                  <input
                    type="text"
                    value={taskId}
                    onChange={(e) => setTaskId(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 border border-slate-800 focus:border-indigo-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">Modelo Selecionado</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 border border-slate-800 focus:border-indigo-500 focus:outline-none"
                >
                  <option value="gemini-2.5-flash">gemini-2.5-flash (Recomendado / Mais rápido e gratuito)</option>
                  <option value="gemini-2.5-pro">gemini-2.5-pro (Raciocínio complexo)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Prompt da Tarefa / Problema a Resolver
                </label>
                <textarea
                  rows={4}
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 p-3 text-xs font-mono text-slate-200 border border-slate-800 focus:border-indigo-500 focus:outline-none leading-relaxed"
                  placeholder="Descreva a alteração ou defeito a ser corrigido..."
                />
              </div>

              {/* Scope Boundary - Crucial for CodePro */}
              <div className="rounded-lg bg-slate-950/70 p-3.5 border border-indigo-900/40 space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs font-semibold text-indigo-300 flex items-center space-x-1.5">
                    <ShieldAlert className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Authorized Scope (Fronteira Autorizada)</span>
                  </label>
                  <span className="text-[10px] text-amber-400 font-mono">FAIL-CLOSED</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Arquivos autorizados (um por linha). Se o modelo tentar modificar qualquer outro arquivo, o chassis <strong>rejeitará o patch</strong> automaticamente.
                </p>
                <textarea
                  rows={3}
                  value={scope}
                  onChange={(e) => setScope(e.target.value)}
                  className="w-full rounded bg-slate-900 px-3 py-2 text-xs font-mono text-emerald-300 border border-slate-800 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Arquivos Candidatos Planejados
                </label>
                <textarea
                  rows={2}
                  value={candidateFiles}
                  onChange={(e) => setCandidateFiles(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 px-3 py-2 text-xs font-mono text-slate-200 border border-slate-800 focus:border-indigo-500 focus:outline-none"
                />
              </div>

              <button
                onClick={handleExecute}
                disabled={isExecuting}
                className="w-full rounded-lg bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/30 transition flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                {isExecuting ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Executando via Gemini & Validando Fronteira...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Disparar Execução Governada</span>
                  </>
                )}
              </button>
            </div>

            {/* Decision Basis Accordion/Box */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-slate-300 font-semibold">
                <Info className="h-4 w-4 text-blue-400" />
                <span>Decision Basis deste Executor (`AGENTS.md`)</span>
              </div>
              <pre className="rounded bg-slate-950 p-3 font-mono text-[11px] text-slate-400 overflow-x-auto border border-slate-800/80">
{`problem_class = coding_agent_governed_model_execution
decision = gemini_structured_code_reasoning_and_patching
basis_type = LOCAL_DESIGN_HYPOTHESIS
basis_ref = docs/decisions/0155-evidence-backed-engineering-decisions.md
supported_claim = Model produces structured analysis within authorized scope
applicability = Governed LLM execution bounded by CodePro scope check
deviation = none`}
              </pre>
            </div>
          </div>

          {/* Right Results: Evidence, Patch, Telemetry */}
          <div className="lg:col-span-6 space-y-4">
            {runResult ? (
              <div className="space-y-4">
                {/* Result Status Banner */}
                <div
                  className={`rounded-xl border p-4 ${
                    runResult.status === 'VERIFIED'
                      ? 'border-emerald-800/80 bg-emerald-950/30 text-emerald-300'
                      : runResult.status === 'REJECTED'
                      ? 'border-rose-800/80 bg-rose-950/30 text-rose-300'
                      : 'border-amber-800/80 bg-amber-950/30 text-amber-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 font-bold text-sm">
                      {runResult.status === 'VERIFIED' ? (
                        <CheckCircle2 className="h-5 w-5 text-emerald-400" />
                      ) : (
                        <XCircle className="h-5 w-5 text-rose-400" />
                      )}
                      <span>STATUS: {runResult.status}</span>
                    </div>
                    <span className="font-mono text-xs text-slate-400">
                      {runResult.duration_ms}ms
                    </span>
                  </div>
                  <p className="mt-1.5 text-xs text-slate-300">{runResult.reason}</p>
                  <div className="mt-2 text-[11px] font-mono text-slate-400">
                    Evidence: {runResult.evidence_root}
                  </div>
                </div>

                {/* Model Summary & Patch */}
                {runResult.model_response && (
                  <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-semibold text-slate-200">
                        Resumo da Solução Gerada
                      </h4>
                      <div className="flex items-center space-x-1">
                        {runResult.model_response.patch && (
                          <button
                            onClick={() => copyPatchToClipboard(runResult.model_response!.patch)}
                            className="flex items-center space-x-1 rounded bg-slate-800 px-2 py-1 text-[11px] text-slate-300 hover:bg-slate-700 transition"
                          >
                            {copiedPatch ? (
                              <Check className="h-3 w-3 text-emerald-400" />
                            ) : (
                              <Copy className="h-3 w-3" />
                            )}
                            <span>{copiedPatch ? 'Copiado!' : 'Copiar Diff'}</span>
                          </button>
                        )}
                      </div>
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed bg-slate-950/60 p-2.5 rounded border border-slate-800/60">
                      {runResult.model_response.summary}
                    </p>

                    <div>
                      <div className="text-[11px] font-mono text-slate-400 mb-1">
                        Arquivos Modificados ({runResult.model_response.proposed_files.length}):
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {runResult.model_response.proposed_files.map((file, idx) => (
                          <span
                            key={idx}
                            className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-indigo-300 border border-slate-700"
                          >
                            {file}
                          </span>
                        ))}
                      </div>
                    </div>

                    {runResult.model_response.patch && (
                      <div>
                        <div className="text-[11px] font-mono text-slate-400 mb-1">Patch / Diff:</div>
                        <pre className="rounded-lg bg-slate-950 p-3 font-mono text-[11px] text-slate-300 overflow-x-auto max-h-72 border border-slate-800">
                          {runResult.model_response.patch}
                        </pre>
                      </div>
                    )}
                  </div>
                )}

                {/* Telemetry Stream */}
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-semibold text-slate-200 flex items-center space-x-2">
                      <Layers className="h-3.5 w-3.5 text-blue-400" />
                      <span>Trilha de Auditoria Telemetria P0 ({runResult.events.length} Eventos)</span>
                    </h4>
                  </div>

                  <div className="space-y-2 max-h-64 overflow-y-auto pr-1">
                    {runResult.events.map((evt, idx) => (
                      <div
                        key={idx}
                        className="rounded-lg bg-slate-950/80 p-2.5 border border-slate-800/80 text-xs font-mono"
                      >
                        <div className="flex items-center justify-between text-[11px]">
                          <span className="font-semibold text-blue-400">{evt.type}</span>
                          <span className="text-slate-500">{new Date(evt.timestamp).toLocaleTimeString()}</span>
                        </div>
                        <div className="mt-1 text-slate-400 text-[11px] overflow-x-auto">
                          {JSON.stringify(evt.data)}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* ADR 0164: Cryptographic Event Chain Audit Card */}
                {runResult.replay_audit && (
                  <div className="rounded-xl border border-emerald-900/60 bg-emerald-950/20 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <ShieldCheck className="h-4 w-4 text-emerald-400" />
                        <h4 className="text-xs font-semibold text-emerald-200">
                          Auditoria Criptográfica de Event-Log (ADR 0164 v1.1)
                        </h4>
                      </div>
                      <span
                        className={`rounded px-2 py-0.5 font-mono text-[10px] font-bold ${
                          runResult.replay_audit.integrity === 'COMPLETE'
                            ? 'bg-emerald-900/80 text-emerald-300 border border-emerald-700'
                            : 'bg-rose-900/80 text-rose-300 border border-rose-700'
                        }`}
                      >
                        {runResult.replay_audit.integrity}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                      <div className="rounded bg-slate-950/90 p-2 border border-slate-800">
                        <span className="text-slate-500 block">Total de Eventos:</span>
                        <span className="text-slate-200 font-bold">{runResult.replay_audit.event_count}</span>
                      </div>
                      <div className="rounded bg-slate-950/90 p-2 border border-slate-800">
                        <span className="text-slate-500 block">Head Digest:</span>
                        <span className="text-emerald-400 truncate block text-[10px]">
                          {runResult.replay_audit.head_digest
                            ? `${runResult.replay_audit.head_digest.slice(0, 16)}...`
                            : 'null'}
                        </span>
                      </div>
                    </div>

                    {runResult.chained_events && runResult.chained_events.length > 0 && (
                      <div className="space-y-1.5 pt-1">
                        <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
                          Elo da Cadeia SHA-256 (Canonical JSON):
                        </div>
                        <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
                          {runResult.chained_events.map((ev) => (
                            <div
                              key={ev.sequence}
                              className="rounded bg-slate-950 p-2 border border-slate-800/80 text-[10px] font-mono space-y-0.5"
                            >
                              <div className="flex justify-between items-center text-slate-400">
                                <span className="text-indigo-400 font-semibold">#{ev.sequence} {ev.event_type}</span>
                                <span className="text-slate-600">prev: {ev.previous_digest ? `${ev.previous_digest.slice(0, 8)}...` : 'null (root)'}</span>
                              </div>
                              <div className="text-emerald-400/90 truncate">
                                sha256: {ev.digest}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500">
                <Bot className="h-10 w-10 mx-auto text-slate-600 mb-3" />
                <p className="text-sm font-medium text-slate-400">Nenhuma execução em andamento</p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  Configure o prompt e o escopo à esquerda e clique em "Disparar Execução Governada" para testar o Gemini.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SUBMODE 2: ASSISTED TASK CHARACTERIZATION */}
      {activeSubMode === 'characterize' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-6 space-y-4">
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                <Sparkles className="h-4 w-4 text-purple-400" />
                <span>Análise de Issue com Gemini (Extração de Sinais P1)</span>
              </h3>
              <p className="text-xs text-slate-400">
                O modelo analisa a descrição da issue e infere os arquivos candidatos, componentes impactados, marcadores de risco e ambiguidade para alimentar o motor determinístico P1 do CodePro.
              </p>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1">
                  Descrição da Issue ou Ticket
                </label>
                <textarea
                  rows={6}
                  value={issueText}
                  onChange={(e) => setIssueText(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 p-3 text-xs font-mono text-slate-200 border border-slate-800 focus:border-purple-500 focus:outline-none leading-relaxed"
                  placeholder="Cole aqui a descrição do bug ou issue do GitHub..."
                />
              </div>

              <button
                onClick={handleCharacterize}
                disabled={charLoading}
                className="w-full rounded-lg bg-purple-600 hover:bg-purple-500 py-2.5 text-xs font-semibold text-white shadow-md shadow-purple-600/30 transition flex items-center justify-center space-x-2 disabled:opacity-50"
              >
                {charLoading ? (
                  <>
                    <RefreshCw className="h-4 w-4 animate-spin" />
                    <span>Extraindo sinais estruturados...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4" />
                    <span>Extrair Sinais com Gemini</span>
                  </>
                )}
              </button>
            </div>
          </div>

          <div className="lg:col-span-6 space-y-4">
            {charOutput ? (
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-white flex items-center space-x-2">
                    <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                    <span>Sinais Estruturados Identificados</span>
                  </h4>
                  {onApplySignalsToP1 && (
                    <button
                      onClick={() =>
                        onApplySignalsToP1({
                          candidate_files: charOutput.candidate_files,
                          affected_components: charOutput.affected_components,
                          ambiguity_markers: charOutput.ambiguity_markers,
                          risk_markers: charOutput.risk_markers,
                        })
                      }
                      className="rounded bg-indigo-600 hover:bg-indigo-500 px-3 py-1 text-xs text-white transition flex items-center space-x-1"
                    >
                      <span>Aplicar na Aba P1</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  )}
                </div>

                <div className="space-y-3 text-xs">
                  <div>
                    <span className="font-mono text-slate-400 block mb-1">
                      Arquivos Candidatos Sugeridos:
                    </span>
                    <div className="rounded bg-slate-950 p-2.5 font-mono text-emerald-300 border border-slate-800">
                      {charOutput.candidate_files.length > 0 ? (
                        charOutput.candidate_files.map((f, i) => <div key={i}>{f}</div>)
                      ) : (
                        <span className="text-slate-500 italic">Nenhum arquivo explícito detectado</span>
                      )}
                    </div>
                  </div>

                  <div>
                    <span className="font-mono text-slate-400 block mb-1">Componentes Impactados:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {charOutput.affected_components.map((c, i) => (
                        <span
                          key={i}
                          className="rounded bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-blue-300 border border-slate-700"
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <span className="font-mono text-slate-400 block mb-1">Marcadores de Risco & Ambiguidade:</span>
                    <div className="flex flex-wrap gap-1.5">
                      {charOutput.risk_markers.map((r, i) => (
                        <span
                          key={i}
                          className="rounded bg-amber-950/80 px-2 py-0.5 font-mono text-[11px] text-amber-300 border border-amber-800"
                        >
                          Risco: {r}
                        </span>
                      ))}
                      {charOutput.ambiguity_markers.map((a, i) => (
                        <span
                          key={i}
                          className="rounded bg-rose-950/80 px-2 py-0.5 font-mono text-[11px] text-rose-300 border border-rose-800"
                        >
                          Ambiguidade: {a}
                        </span>
                      ))}
                    </div>
                  </div>

                  {charOutput.reasoning && (
                    <div>
                      <span className="font-mono text-slate-400 block mb-1">Justificativa do Modelo:</span>
                      <p className="text-slate-300 bg-slate-950 p-3 rounded border border-slate-800 leading-relaxed">
                        {charOutput.reasoning}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500">
                <Sparkles className="h-10 w-10 mx-auto text-slate-600 mb-3" />
                <p className="text-sm font-medium text-slate-400">Aguardando análise</p>
                <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
                  Escreva ou cole a descrição da issue no campo à esquerda para o Gemini caracterizar os sinais de engenharia.
                </p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
