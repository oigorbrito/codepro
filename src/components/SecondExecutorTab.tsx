import React, { useState } from 'react';
import {
  Users,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  RefreshCw,
  Cpu,
  Layers,
  ArrowRight,
  GitBranch,
  Terminal,
  FileCode,
} from 'lucide-react';
import {
  EXECUTOR_REGISTRY,
  runPairedQualificationComparison,
  PairedComparisonReport,
} from '../chassis/secondExecutorQualification';

export const SecondExecutorTab: React.FC = () => {
  const [report, setReport] = useState<PairedComparisonReport | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRunPairedComparison = () => {
    setLoading(true);
    setTimeout(() => {
      try {
        const result = runPairedQualificationComparison();
        setReport(result);
      } finally {
        setLoading(false);
      }
    }, 400);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center space-x-2">
            <Users className="h-5 w-5 text-indigo-400" />
            <span>ADR 0152 — Aprovação & Qualificação do 2º Executor</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Matriz de auditoria de executores concorrentes e execução pareada para validação de independência (P8.2 / Baseline v1).
          </p>
        </div>

        <button
          onClick={handleRunPairedComparison}
          disabled={loading}
          className="flex items-center space-x-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Executando Par...' : 'Executar Comparação Pareada'}</span>
        </button>
      </div>

      {/* Regras Normativas de AGENTS.md / ADR 0152 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono text-xs">
        <div className="rounded-lg bg-slate-900/60 border border-slate-800 p-3 space-y-1">
          <div className="text-indigo-400 font-bold">SAME_NAME != SAME_TREATMENT</div>
          <div className="text-slate-400 text-[11px]">
            Variar apenas o modelo de LLM sobre o mesmo runner não cria um segundo executor.
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/60 border border-slate-800 p-3 space-y-1">
          <div className="text-amber-400 font-bold">NO_SILENT_SWITCH</div>
          <div className="text-slate-400 text-[11px]">
            É proibido alternar dinamicamente entre executores se um deles falhar na tarefa.
          </div>
        </div>
        <div className="rounded-lg bg-slate-900/60 border border-slate-800 p-3 space-y-1">
          <div className="text-emerald-400 font-bold">PARIDADE DE VERIFICAÇÃO</div>
          <div className="text-slate-400 text-[11px]">
            Ambos devem submeter-se ao mesmo verifier independente (pytest), escopo e timeout.
          </div>
        </div>
      </div>

      {/* Matriz de Pré-voo de Candidatos */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold text-sm text-slate-200 flex items-center space-x-2">
            <Cpu className="h-4 w-4 text-blue-400" />
            <span>Matriz de Candidatos a Executor (Preflight Audit)</span>
          </h3>
          <span className="text-[10px] font-mono text-slate-500">ADR 0152 PREFLIGHT REGISTRY</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
          {Object.values(EXECUTOR_REGISTRY).map((exec) => (
            <div
              key={exec.executor_id}
              className={`rounded-lg p-3 border space-y-2 ${
                exec.qualification_status === 'QUALIFIED'
                  ? 'border-emerald-800/80 bg-emerald-950/20'
                  : 'border-slate-800 bg-slate-950/40'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-slate-200">{exec.name}</span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                    exec.qualification_status === 'QUALIFIED'
                      ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                      : exec.qualification_status === 'BLOCKED_RUNTIME'
                      ? 'bg-amber-950 text-amber-300 border border-amber-800'
                      : 'bg-rose-950 text-rose-300 border border-rose-800'
                  }`}
                >
                  {exec.qualification_status}
                </span>
              </div>
              <div className="text-[11px] text-slate-400 space-y-0.5">
                <div>• Runtime: <span className="text-slate-300">{exec.runtime}</span></div>
                <div>• Headless: <span className="text-slate-300">{String(exec.headless)}</span></div>
                <div>• Digest: <span className="text-slate-500">{exec.config_digest.slice(0, 16)}...</span></div>
                <div className="text-slate-500 text-[10px] pt-1">{exec.qualification_notes}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Resultado da Comparação Pareada */}
      {report && (
        <div className="space-y-4">
          <div
            className={`rounded-xl border p-4 flex items-center justify-between ${
              report.classification === 'PAIRED_QUALIFICATION_SUCCESS'
                ? 'border-emerald-800 bg-emerald-950/40 text-emerald-200'
                : 'border-rose-800 bg-rose-950/40 text-rose-200'
            }`}
          >
            <div className="flex items-center space-x-3">
              {report.classification === 'PAIRED_QUALIFICATION_SUCCESS' ? (
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
              ) : (
                <AlertOctagon className="h-6 w-6 text-rose-400" />
              )}
              <div>
                <div className="font-mono text-sm font-bold">{report.classification}</div>
                <div className="text-xs opacity-80">
                  Paridade comprovada entre o executor primário (mini-swe-agent) e o segundo executor aprovado (gemini-structured-code-agent).
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono opacity-70">
              {new Date(report.timestamp).toLocaleTimeString()}
            </span>
          </div>

          {/* Cards Lado a Lado */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
            {/* Primary Executor */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-indigo-400 font-bold">1º Executor (Primário)</span>
                <span className="text-emerald-400 font-bold">{report.primary_executor.status}</span>
              </div>
              <div className="space-y-1 text-slate-300 text-[11px]">
                <div>• Executor ID: <span className="text-slate-100">{report.primary_executor.executor_id}</span></div>
                <div>• Run ID: <span className="text-slate-400 text-[10px]">{report.primary_executor.run_id}</span></div>
                <div>• Verifier Status: <span className="text-emerald-400">{report.primary_executor.verifier_status}</span></div>
                <div>• Duração: <span className="text-slate-300">{report.primary_executor.duration_ms}ms</span></div>
                <div>• Patch SHA-256: <span className="text-slate-500 text-[10px]">{report.primary_executor.patch_sha256.slice(0, 16)}...</span></div>
              </div>
            </div>

            {/* Secondary Executor */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-purple-400 font-bold">2º Executor (Aprovado ADR 0152)</span>
                <span className="text-emerald-400 font-bold">{report.secondary_executor.status}</span>
              </div>
              <div className="space-y-1 text-slate-300 text-[11px]">
                <div>• Executor ID: <span className="text-slate-100">{report.secondary_executor.executor_id}</span></div>
                <div>• Run ID: <span className="text-slate-400 text-[10px]">{report.secondary_executor.run_id}</span></div>
                <div>• Verifier Status: <span className="text-emerald-400">{report.secondary_executor.verifier_status}</span></div>
                <div>• Duração: <span className="text-slate-300">{report.secondary_executor.duration_ms}ms</span></div>
                <div>• Patch SHA-256: <span className="text-slate-500 text-[10px]">{report.secondary_executor.patch_sha256.slice(0, 16)}...</span></div>
              </div>
            </div>
          </div>

          {/* Teste Empírico Autorizado do OpenHands */}
          {report.openhands_empirical_test && (
            <div className="rounded-xl border border-amber-900/80 bg-amber-950/20 p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between border-b border-amber-800/40 pb-2">
                <span className="text-amber-400 font-bold flex items-center space-x-2">
                  <span>TESTE EMPÍRICO OPENHANDS CLI v1.21.0 (BYPASS AUTORIZADO)</span>
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded font-bold bg-amber-900/60 text-amber-200 border border-amber-700">
                  {report.openhands_empirical_test.execution_result}
                </span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                <div className="space-y-1 text-slate-300">
                  <div>• Autorização: <span className="text-amber-300">{report.openhands_empirical_test.authorized_by}</span></div>
                  <div>• Diretiva de Ambiente: <span className="text-slate-400">{report.openhands_empirical_test.runtime_override}</span></div>
                  <div>• Caminho de Cache: <span className="text-slate-400">{report.openhands_empirical_test.cache_path_resolved}</span></div>
                </div>
                <div className="space-y-1 text-slate-300">
                  <div>• Benchmark Base (SWE-bench Verified): <span className="text-emerald-400 font-bold">{report.openhands_empirical_test.benchmark_baseline_verified_pct}%</span></div>
                  <div>• Tokens In / Out: <span className="text-slate-400">{report.openhands_empirical_test.raw_telemetry.tokens_in} / {report.openhands_empirical_test.raw_telemetry.tokens_out}</span></div>
                  <div>• Tempo de Resposta: <span className="text-slate-400">{report.openhands_empirical_test.raw_telemetry.wall_time_ms}ms</span> | Exit Code: <span className="text-emerald-400">{report.openhands_empirical_test.raw_telemetry.return_code}</span></div>
                </div>
              </div>
            </div>
          )}

          {/* Decision Record Formatado */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2 font-mono text-xs">
            <div className="text-slate-300 font-semibold">DECISION BASIS FORMAL (AGENTS.md)</div>
            <pre className="rounded bg-slate-950 p-3 text-emerald-400 text-[11px] overflow-x-auto border border-slate-800">
{`problem_class = ${report.decision_record.problem_class}
decision = ${report.decision_record.decision}
basis_type = ${report.decision_record.basis_type}
basis_ref = ${report.decision_record.basis_ref}
supported_claim = ${report.decision_record.supported_claim}
applicability = ${report.decision_record.applicability}
deviation = ${report.decision_record.deviation}`}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};
