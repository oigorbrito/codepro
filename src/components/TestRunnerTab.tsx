import React, { useState } from 'react';
import {
  PlayCircle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Flame,
  Terminal,
  Clock,
  ShieldCheck,
  Cpu,
  Layers,
  FileCheck,
  Compass,
} from 'lucide-react';

interface TestSuiteResult {
  file: string;
  label: string;
  passed: boolean;
  duration_ms: number;
  output: string;
  exit_code: number;
}

interface TestRunSummary {
  timestamp: string;
  total_suites: number;
  passed_suites: number;
  all_passed: boolean;
  results: TestSuiteResult[];
}

export const TestRunnerTab: React.FC = () => {
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<TestRunSummary | null>(null);
  const [activeOutputIndex, setActiveOutputIndex] = useState<number | null>(null);

  const handleRunAllTests = async () => {
    setRunning(true);
    try {
      const res = await fetch('/api/tests/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      });
      const data: TestRunSummary = await res.json();
      setResults(data);
    } catch (err) {
      console.error('Falha ao executar suítes de teste:', err);
    } finally {
      setRunning(false);
    }
  };

  const suiteDescriptions: Record<string, string> = {
    'test_blind_spot.ts': 'Stress test de degradação de contexto (1, 2, 4 e 8 arquivos). Avalia o ponto de quebra dos 5 modelos modestos.',
    'test_event_log.ts': 'Auditoria de integridade criptográfica da cadeia de eventos e telemetria SHA-256 (ADR 0164).',
    'test_m2_m3_gates.ts': 'Portões anti-falso positivo e verificação de reprodutibilidade determinística (Issue #57).',
    'test_pr40_hardening.ts': 'Blindagem léxica e guarda contra expansão silenciosa de escopo no workspace (Issue #40).',
    'test_second_executor.ts': 'Preflight e teste pareado de qualificação do OpenHands CLI como 2º executor oficial (ADR 0152).',
    'test_tiered_routing.ts': 'Motor de roteamento cirúrgico de tarefas para Tiers 1, 2 e 3 baseado em complexidade e hardware.',
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header Banner */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <ShieldCheck className="h-6 w-6 text-emerald-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Central de Verificação e Execução Contínua de Testes
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Dispare sob demanda as 6 suítes formais do CodePro com saída em tempo real e verificação de integridade zero-falso-positivo.
            </p>
          </div>

          <button
            onClick={handleRunAllTests}
            disabled={running}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-semibold text-xs transition shadow-md shadow-emerald-950 font-mono"
          >
            <RefreshCw className={`h-4 w-4 ${running ? 'animate-spin' : ''}`} />
            <span>{running ? 'EXECUTANDO SUÍTES...' : 'DISPARAR TODOS OS TESTES'}</span>
          </button>
        </div>

        {/* Status Pills */}
        <div className="mt-5 grid grid-cols-2 md:grid-cols-4 gap-3 font-mono text-xs">
          <div className="rounded-lg bg-slate-950 border border-slate-800 p-2.5">
            <div className="text-[10px] text-slate-500 uppercase">Suítes Oficiais</div>
            <div className="font-bold text-slate-200 mt-0.5">6 Arquivos de Teste</div>
          </div>
          <div className="rounded-lg bg-slate-950 border border-slate-800 p-2.5">
            <div className="text-[10px] text-slate-500 uppercase">Status do 2º Executor</div>
            <div className="font-bold text-emerald-400 mt-0.5">QUALIFIED (OpenHands)</div>
          </div>
          <div className="rounded-lg bg-slate-950 border border-slate-800 p-2.5">
            <div className="text-[10px] text-slate-500 uppercase">Modelos Avaliados</div>
            <div className="font-bold text-blue-400 mt-0.5">5 Modelos Modestos</div>
          </div>
          <div className="rounded-lg bg-slate-950 border border-slate-800 p-2.5">
            <div className="text-[10px] text-slate-500 uppercase">Último Resultado</div>
            <div className="font-bold text-slate-300 mt-0.5">
              {results ? (
                results.all_passed ? (
                  <span className="text-emerald-400">100% APROVADO ({results.passed_suites}/{results.total_suites})</span>
                ) : (
                  <span className="text-rose-400">FALHAS DETECTADAS</span>
                )
              ) : (
                <span className="text-slate-500">Pronto para rodar</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Resultados dos Testes */}
      {results && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-slate-200 font-mono">
              Relatório de Execução ({results.timestamp})
            </h3>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
              Taxa de Sucesso: {((results.passed_suites / results.total_suites) * 100).toFixed(0)}%
            </span>
          </div>

          <div className="grid grid-cols-1 gap-3">
            {results.results.map((suite, idx) => (
              <div
                key={suite.file}
                className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 hover:border-slate-700 transition"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-2">
                  <div className="flex items-center space-x-3">
                    {suite.passed ? (
                      <CheckCircle2 className="h-5 w-5 text-emerald-400 shrink-0" />
                    ) : (
                      <XCircle className="h-5 w-5 text-rose-400 shrink-0" />
                    )}
                    <div>
                      <div className="font-bold text-sm text-slate-200 font-mono flex items-center space-x-2">
                        <span>{suite.label}</span>
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                          tests/{suite.file}
                        </span>
                      </div>
                      <div className="text-xs text-slate-400 mt-0.5">
                        {suiteDescriptions[suite.file] || 'Verificação automatizada do sistema.'}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-3 text-xs font-mono">
                    <span className="text-slate-400 flex items-center space-x-1">
                      <Clock className="h-3.5 w-3.5" />
                      <span>{suite.duration_ms}ms</span>
                    </span>
                    <button
                      onClick={() => setActiveOutputIndex(activeOutputIndex === idx ? null : idx)}
                      className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition text-[11px]"
                    >
                      {activeOutputIndex === idx ? 'Ocultar Terminal' : 'Ver Saída'}
                    </button>
                  </div>
                </div>

                {/* Terminal de Saída Expansível */}
                {activeOutputIndex === idx && (
                  <div className="mt-3 pt-3 border-t border-slate-800/80">
                    <div className="rounded-lg bg-slate-950 p-3 font-mono text-[11px] text-slate-300 whitespace-pre-wrap overflow-x-auto max-h-60 border border-slate-800">
                      {suite.output}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Guia Rápido dos Testes */}
      {!results && (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-950/40 p-8 text-center space-y-3">
          <Terminal className="h-8 w-8 text-slate-500 mx-auto" />
          <div className="font-semibold text-slate-300 text-sm">
            Clique no botão acima para rodar a suíte completa de ponta a ponta
          </div>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Cada teste executa um harness TypeScript real que audita desde os gates criptográficos e limites de contexto até a qualificação do segundo executor.
          </p>
        </div>
      )}
    </div>
  );
};
