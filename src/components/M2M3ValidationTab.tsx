import React, { useState } from 'react';
import {
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  ShieldCheck,
  Clock,
  ServerCrash,
  Layers,
  ArrowRight,
} from 'lucide-react';
import {
  validateM2M3Gate,
  M2M3ValidationReport,
  ISSUE_57_FROZEN_SPEC,
} from '../chassis/m2m3Validation';

export const M2M3ValidationTab: React.FC = () => {
  const [report, setReport] = useState<M2M3ValidationReport | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRunValidation = () => {
    setLoading(true);
    setTimeout(() => {
      try {
        const result = validateM2M3Gate();
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
            <Layers className="h-5 w-5 text-indigo-400" />
            <span>MVP Gates M2 & M3 Validation Harness</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Verificação combinada dos gates normativos M2 (estados negativos sem falso sucesso) e M3 (repetição controlada idempotente da Issue #57).
          </p>
        </div>

        <button
          onClick={handleRunValidation}
          disabled={loading}
          className="flex items-center space-x-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Executando Gates...' : 'Executar Validação M2 + M3'}</span>
        </button>
      </div>

      {/* Target Spec Card */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2 font-mono text-xs">
        <div className="text-slate-300 font-semibold flex items-center justify-between">
          <span>ESPECIFICAÇÃO CONGELADA DA ISSUE #57 (ADR 0156 / MVP-SCOPE)</span>
          <span className="text-[10px] text-indigo-400 bg-indigo-950 px-2 py-0.5 rounded border border-indigo-800">
            FROZEN TARGET
          </span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-slate-400 text-[11px]">
          <div>• Base SHA: <span className="text-slate-200">{ISSUE_57_FROZEN_SPEC.BASE_SHA}</span></div>
          <div>• Task ID: <span className="text-slate-200">{ISSUE_57_FROZEN_SPEC.TASK_ID}</span></div>
          <div>• Scope: <span className="text-slate-200">{ISSUE_57_FROZEN_SPEC.SCOPE.join(', ')}</span></div>
          <div>• Verifier: <span className="text-slate-200">{ISSUE_57_FROZEN_SPEC.VERIFIER_ARGV.join(' ')}</span></div>
        </div>
      </div>

      {/* Results View */}
      {report ? (
        <div className="space-y-6">
          {/* Classification Banner */}
          <div
            className={`rounded-xl border p-4 flex items-center justify-between ${
              report.classification === 'M2_M3_VALIDATED'
                ? 'border-emerald-800 bg-emerald-950/40 text-emerald-200'
                : 'border-rose-800 bg-rose-950/40 text-rose-200'
            }`}
          >
            <div className="flex items-center space-x-3">
              {report.classification === 'M2_M3_VALIDATED' ? (
                <CheckCircle2 className="h-6 w-6 text-emerald-400" />
              ) : (
                <AlertOctagon className="h-6 w-6 text-rose-400" />
              )}
              <div>
                <div className="font-mono text-sm font-bold">{report.classification}</div>
                <div className="text-xs opacity-80">
                  {report.classification === 'M2_M3_VALIDATED'
                    ? 'Todos os estados negativos M2 foram rejeitados sem falso sucesso e os dois ciclos M3 atingiram determinismo de patch idêntico.'
                    : 'Falha em um ou mais critérios normativos dos gates M2/M3.'}
                </div>
              </div>
            </div>
            <span className="text-[10px] font-mono opacity-70">
              {new Date(report.timestamp).toLocaleTimeString()}
            </span>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Gate M2 Block */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <AlertOctagon className="h-4 w-4 text-amber-400" />
                  <h3 className="font-semibold text-sm text-slate-200">Gate M2: Estados Negativos</h3>
                </div>
                <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800 px-2 py-0.5 rounded">
                  ZERO FALSE SUCCESS
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {/* 1. Nonzero exit */}
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800/80 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 flex items-center space-x-1.5">
                      <ServerCrash className="h-3.5 w-3.5 text-rose-400" />
                      <span>Non-zero Executor Exit:</span>
                    </span>
                    <span className="text-rose-400 font-bold">{report.m2_results.nonzero_exit.status}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Garantia: Impedir status VERIFIED quando returncode != 0
                  </div>
                </div>

                {/* 2. Timeout */}
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800/80 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 flex items-center space-x-1.5">
                      <Clock className="h-3.5 w-3.5 text-amber-400" />
                      <span>Command Timeout:</span>
                    </span>
                    <span className="text-amber-400 font-bold">{report.m2_results.command_timeout.status}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Garantia: Rejeitar após estouro de max_wall_time_seconds
                  </div>
                </div>

                {/* 3. Environment unavailable */}
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800/80 space-y-1">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 flex items-center space-x-1.5">
                      <AlertOctagon className="h-3.5 w-3.5 text-blue-400" />
                      <span>Environment Unavailable:</span>
                    </span>
                    <span className="text-blue-400 font-bold">{report.m2_results.environment_unavailable.status}</span>
                  </div>
                  <div className="text-[10px] text-slate-500">
                    Garantia: Falhar de forma estrita se executável não existir
                  </div>
                </div>
              </div>
            </div>

            {/* Gate M3 Block */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="h-4 w-4 text-emerald-400" />
                  <h3 className="font-semibold text-sm text-slate-200">Gate M3: Repetição Controlada</h3>
                </div>
                <span className="text-[10px] font-mono bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded">
                  IDEMPOTENT PAIR
                </span>
              </div>

              <div className="space-y-3 font-mono text-xs">
                {/* Cycles Comparison */}
                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="rounded bg-slate-950 p-2.5 border border-slate-800 space-y-1">
                    <div className="text-indigo-400 font-semibold">Ciclo 1 ({report.m3_results.cycle_1.attempt_id})</div>
                    <div className="text-slate-400 text-[10px] truncate">ID: {report.m3_results.cycle_1.run_id}</div>
                    <div className="text-emerald-400 font-bold">{report.m3_results.cycle_1.status}</div>
                    <div className="text-[9px] text-slate-500 truncate">sha: {report.m3_results.cycle_1.patch_sha256.slice(0, 16)}...</div>
                  </div>

                  <div className="rounded bg-slate-950 p-2.5 border border-slate-800 space-y-1">
                    <div className="text-indigo-400 font-semibold">Ciclo 2 ({report.m3_results.cycle_2.attempt_id})</div>
                    <div className="text-slate-400 text-[10px] truncate">ID: {report.m3_results.cycle_2.run_id}</div>
                    <div className="text-emerald-400 font-bold">{report.m3_results.cycle_2.status}</div>
                    <div className="text-[9px] text-slate-500 truncate">sha: {report.m3_results.cycle_2.patch_sha256.slice(0, 16)}...</div>
                  </div>
                </div>

                {/* Validation checklist */}
                <div className="rounded-lg bg-slate-950 p-3 border border-slate-800/80 space-y-1.5 text-[11px]">
                  <div className="flex items-center justify-between text-slate-300">
                    <span>• Ambos atingiram VERIFIED:</span>
                    <span className="text-emerald-400 font-bold">{String(report.m3_results.both_verified)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>• Tentativas com attempt_id distintos:</span>
                    <span className="text-emerald-400 font-bold">{String(report.m3_results.distinct_attempt_id)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>• Evidências com run_id distintos:</span>
                    <span className="text-emerald-400 font-bold">{String(report.m3_results.distinct_run_id)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>• Conjunto changed_files idêntico:</span>
                    <span className="text-emerald-400 font-bold">{String(report.m3_results.same_changed_files)}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span>• Hash SHA-256 do patch idêntico:</span>
                    <span className="text-emerald-400 font-bold">{String(report.m3_results.same_patch_sha256)}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500 space-y-3">
          <Layers className="h-10 w-10 mx-auto text-slate-600" />
          <div className="text-sm font-medium text-slate-400">Harness de Gates M2 + M3 pronto para execução</div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Clique no botão acima para rodar a bateria completa de 3 testes negativos (M2) e 2 ciclos de repetição determinística da Issue #57 (M3).
          </p>
        </div>
      )}
    </div>
  );
};
