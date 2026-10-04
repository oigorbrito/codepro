import React, { useState, useEffect } from 'react';
import {
  Cpu,
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Play,
  Terminal,
  FileCode,
  Shield,
  Layers,
  Settings2,
  ExternalLink,
  Flame,
} from 'lucide-react';
import { OllamaModelInfo, OllamaExecuteResponse } from '../chassis/ollamaRunner';

export const LocalOllamaTab: React.FC = () => {
  const [endpoint, setEndpoint] = useState('http://127.0.0.1:11434');
  const [checking, setChecking] = useState(false);
  const [statusData, setStatusData] = useState<{
    connected: boolean;
    models: OllamaModelInfo[];
    error?: string;
  } | null>(null);

  // Formulário de Execução
  const [selectedModel, setSelectedModel] = useState<string>('qwen2.5-coder:7b');
  const [taskPrompt, setTaskPrompt] = useState(
    'Corrigir a função de validação de scope em src/chassis/vertical.ts para garantir que nenhum arquivo fora de authorized_scope seja lido ou modificado.'
  );
  const [scopeFiles, setScopeFiles] = useState('src/chassis/vertical.ts');
  const [temperature, setTemperature] = useState(0.1);
  const [maxTokens, setMaxTokens] = useState(2048);

  const [executing, setExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<OllamaExecuteResponse | null>(null);

  const checkConnection = async () => {
    setChecking(true);
    try {
      const res = await fetch(`/api/ollama/status?endpoint=${encodeURIComponent(endpoint)}`);
      const data = await res.json();
      setStatusData(data);
      if (data.models && data.models.length > 0) {
        setSelectedModel(data.models[0].name);
      }
    } catch (err: any) {
      setStatusData({
        connected: false,
        models: [],
        error: err.message,
      });
    } finally {
      setChecking(false);
    }
  };

  useEffect(() => {
    checkConnection();
  }, []);

  const handleExecute = async (forceSimulation = false) => {
    setExecuting(true);
    setExecutionResult(null);
    try {
      const filesArray = scopeFiles
        .split('\n')
        .map((f) => f.trim())
        .filter((f) => f.length > 0);

      const res = await fetch('/api/ollama/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          endpoint,
          model: selectedModel,
          task_prompt: taskPrompt,
          scope_files: filesArray,
          temperature,
          max_tokens: maxTokens,
          simulation_mode: forceSimulation || !statusData?.connected,
        }),
      });
      const data: OllamaExecuteResponse = await res.json();
      setExecutionResult(data);
    } catch (err: any) {
      setExecutionResult({
        run_id: 'err-' + Date.now(),
        model: selectedModel,
        status: 'FAILED',
        duration_ms: 0,
        patch: '',
        files_modified: [],
        scope_adherent: false,
        raw_response: '',
        error: `Falha na requisição: ${err.message}. (Verifique se o backend do CodePro consegue alcançar o endpoint ou use o Modo Harness/Simulação).`,
      });
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Banner de Conexão */}
      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-6 shadow-lg space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Cpu className="h-6 w-6 text-purple-400" />
              <h2 className="text-lg font-bold text-slate-100">
                Ponte Local Ollama (Hardware Real &amp; Modelos Modestos)
              </h2>
            </div>
            <p className="text-xs text-slate-400">
              Conexão direta com a sua instância do Ollama (<code className="text-purple-300 font-mono">localhost:11434</code>) sob governança estrita de escopo (CodePro ADR 0159).
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <div className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-800 text-xs font-mono">
              <span className="text-slate-400">Endpoint:</span>
              <input
                type="text"
                value={endpoint}
                onChange={(e) => setEndpoint(e.target.value)}
                className="bg-transparent text-slate-200 outline-none w-44"
              />
            </div>
            <button
              onClick={checkConnection}
              disabled={checking}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-slate-200 text-xs font-mono flex items-center space-x-1.5 transition"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${checking ? 'animate-spin' : ''}`} />
              <span>{checking ? 'Testando...' : 'Reconectar'}</span>
            </button>
          </div>
        </div>

        {/* Card de Status da Conexão */}
        <div className="rounded-lg bg-slate-950 border border-slate-800 p-4">
          {statusData?.connected ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2 text-emerald-400 font-semibold text-xs font-mono">
                  <CheckCircle className="h-4 w-4" />
                  <span>Ollama Conectado com Sucesso! ({statusData.models.length} modelos locais detectados)</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  DAEMON ONLINE
                </span>
              </div>

              {/* Lista de Modelos Locais */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2 pt-1 font-mono text-xs">
                {statusData.models.map((m) => (
                  <div
                    key={m.digest || m.name}
                    onClick={() => setSelectedModel(m.name)}
                    className={`p-2.5 rounded border cursor-pointer transition ${
                      selectedModel === m.name
                        ? 'border-purple-500 bg-purple-950/30 text-purple-200'
                        : 'border-slate-800 bg-slate-900/60 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold flex items-center justify-between">
                      <span className="truncate">{m.name}</span>
                      <span className="text-[10px] text-slate-500">{m.recommended_tier}</span>
                    </div>
                    <div className="text-[10px] text-slate-500 mt-1">
                      Tamanho: {(m.size / (1024 * 1024 * 1024)).toFixed(1)} GB
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-2 text-xs">
              <div className="flex items-center space-x-2 text-amber-400 font-mono font-semibold">
                <AlertTriangle className="h-4 w-4" />
                <span>Ollama Local Não Detectado em {endpoint}</span>
              </div>
              <p className="text-slate-400">
                Se o seu Ollama já estiver instalado no seu computador, certifique-se de que ele está ativo:
              </p>
              <div className="p-2.5 rounded bg-slate-900 border border-slate-800 font-mono text-purple-300 text-[11px]">
                ollama serve # para subir o daemon localmente<br />
                ollama run qwen2.5-coder:7b # para baixar o modelo recomendado
              </div>
              <p className="text-[11px] text-slate-500">
                Caso você queira testar a interface mesmo sem o daemon rodando neste container, os modelos sugeridos já estão pré-configurados abaixo.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Painel de Execução de Tarefa Governada */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Coluna da Esquerda: Configurações e Prompt */}
        <div className="md:col-span-2 space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="font-bold text-sm text-slate-200 font-mono flex items-center space-x-2">
              <Play className="h-4 w-4 text-emerald-400" />
              <span>Executar Tarefa com Modelo Local</span>
            </h3>

            {/* Seleção do Modelo */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Modelo Selecionado:</label>
              <input
                type="text"
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                placeholder="ex: granite3.1-dense:8b, granite-code:8b, codellama:7b, qwen2.5-coder:7b"
                className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2.5 text-xs font-mono text-slate-200 focus:border-purple-500 outline-none"
              />
              <div className="flex flex-wrap gap-1.5 mt-2">
                {[
                  { tag: 'granite3.1-dense:8b', label: 'IBM Granite 3.1 8B (128k)', tier: 'Tier 1/2' },
                  { tag: 'granite-code:8b', label: 'IBM Granite Code 8B', tier: 'Tier 1/2' },
                  { tag: 'codellama:7b', label: 'CodeLlama 7B (Meta)', tier: 'Tier 1' },
                  { tag: 'codellama:13b', label: 'CodeLlama 13B (Meta)', tier: 'Tier 2' },
                  { tag: 'qwen2.5-coder:7b', label: 'Qwen 2.5 Coder 7B', tier: 'Tier 1' },
                  { tag: 'qwen2.5-coder:14b', label: 'Qwen 2.5 Coder 14B', tier: 'Tier 2' },
                  { tag: 'deepseek-coder:6.7b', label: 'DeepSeek 6.7B', tier: 'Tier 1' },
                  { tag: 'qwen2.5-coder:3b', label: 'Qwen 3B (Ultra-leve)', tier: 'Tier 1' },
                ].map((preset) => (
                  <button
                    key={preset.tag}
                    onClick={() => setSelectedModel(preset.tag)}
                    className={`text-[10px] font-mono px-2.5 py-1 rounded border transition flex items-center space-x-1.5 ${
                      selectedModel === preset.tag
                        ? 'bg-purple-950 text-purple-200 border-purple-500 font-bold'
                        : 'bg-slate-800/80 text-slate-300 border-slate-700 hover:bg-slate-700'
                    }`}
                  >
                    <span>{preset.tag}</span>
                    <span className="text-[9px] text-slate-400 font-normal">({preset.tier})</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Prompt da Tarefa */}
            <div>
              <label className="block text-xs font-mono text-slate-400 mb-1">Instrução / Especificação da Tarefa:</label>
              <textarea
                rows={4}
                value={taskPrompt}
                onChange={(e) => setTaskPrompt(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2.5 text-xs font-mono text-slate-200 focus:border-purple-500 outline-none resize-none"
              />
            </div>

            {/* Arquivos no Escopo */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="text-xs font-mono text-slate-400">
                  Arquivos Autorizados no Escopo (1 por linha):
                </label>
                <span className="text-[10px] font-mono text-amber-400">
                  NO_SILENT_SCOPE_EXPANSION ATIVO
                </span>
              </div>
              <textarea
                rows={2}
                value={scopeFiles}
                onChange={(e) => setScopeFiles(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2.5 text-xs font-mono text-slate-200 focus:border-purple-500 outline-none"
              />
            </div>

            {/* Botões de Disparo */}
            <div className="space-y-2">
              <button
                onClick={() => handleExecute(false)}
                disabled={executing || !taskPrompt}
                className="w-full flex items-center justify-center space-x-2 px-4 py-3 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-semibold text-xs font-mono transition shadow-lg shadow-purple-950"
              >
                <Play className={`h-4 w-4 ${executing ? 'animate-pulse' : ''}`} />
                <span>{executing ? 'EXECUTANDO NO MODELO LOCAL...' : 'EXECUTAR TAREFA NO OLLAMA LOCAL'}</span>
              </button>

              <button
                onClick={() => handleExecute(true)}
                disabled={executing || !taskPrompt}
                className="w-full flex items-center justify-center space-x-2 px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-purple-300 border border-purple-900/60 font-medium text-xs font-mono transition"
              >
                <Shield className="h-3.5 w-3.5 text-purple-400" />
                <span>RODAR TESTE DE HARNESS DO VIGIA (SIMULAÇÃO GOVERNADA)</span>
              </button>
            </div>
          </div>
        </div>

        {/* Coluna da Direita: Parâmetros e Travas de Governança */}
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4 text-xs font-mono">
            <h4 className="font-bold text-slate-200 flex items-center space-x-1.5">
              <Shield className="h-4 w-4 text-emerald-400" />
              <span>Travas de Governança</span>
            </h4>

            <div className="space-y-2 text-[11px] text-slate-400">
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <span>Modo de Operação:</span>
                <span className="text-purple-300 font-bold">Local Open-Weights</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <span>Custo por Token:</span>
                <span className="text-emerald-400 font-bold">$0.00 (Zero Custo)</span>
              </div>
              <div className="flex items-center justify-between border-b border-slate-800 pb-1.5">
                <span>Auditoria de Escopo:</span>
                <span className="text-blue-400 font-bold">Verificação Léxica</span>
              </div>
              <div className="flex items-center justify-between pb-1">
                <span>Captura de Patch:</span>
                <span className="text-amber-400 font-bold">Extração Unificada</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-800 space-y-3">
              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Temperature ({temperature})</label>
                <input
                  type="range"
                  min="0.0"
                  max="1.0"
                  step="0.05"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                  className="w-full accent-purple-500"
                />
              </div>

              <div>
                <label className="text-[10px] text-slate-500 uppercase block mb-1">Max Tokens ({maxTokens})</label>
                <input
                  type="number"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value) || 1024)}
                  className="w-full rounded bg-slate-950 border border-slate-800 px-2 py-1 text-slate-200 outline-none"
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Resultado da Execução */}
      {executionResult && (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center space-x-2">
              <Terminal className="h-5 w-5 text-purple-400" />
              <h3 className="font-bold text-sm text-slate-200 font-mono">
                Resultado da Execução: {executionResult.run_id}
              </h3>
            </div>
            <div className="flex items-center space-x-3 text-xs font-mono">
              <span className="text-slate-400">Duração: {executionResult.duration_ms}ms</span>
              {executionResult.status === 'COMPLETED' ? (
                <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 font-bold">
                  ✓ COMPLETED
                </span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800 font-bold">
                  ✗ {executionResult.status}
                </span>
              )}
            </div>
          </div>

          {executionResult.error ? (
            <div className="space-y-3">
              <div className="rounded-lg bg-rose-950/40 border border-rose-900 p-4 text-rose-300 font-mono text-xs space-y-2">
                <div className="flex items-center space-x-2 font-bold text-rose-200">
                  <XCircle className="h-4 w-4 text-rose-400" />
                  <span>Erro de Execução / Comunicação com o Executor:</span>
                </div>
                <div className="text-[11px] leading-relaxed">{executionResult.error}</div>
              </div>

              <div className="rounded-lg bg-slate-950 border border-slate-800 p-4 font-mono text-xs space-y-2 text-slate-300">
                <div className="text-amber-400 font-bold flex items-center space-x-1.5">
                  <AlertTriangle className="h-4 w-4" />
                  <span>Por que o erro "fetch failed" aconteceu?</span>
                </div>
                <p className="text-[11px] text-slate-400">
                  O CodePro está rodando em um servidor em nuvem (Google Cloud) e não tem rota de rede direta para o IP privado <code className="text-purple-300">127.0.0.1</code> da sua máquina pessoal.
                </p>
                <div className="p-2.5 rounded bg-slate-900 border border-slate-800 text-[11px] text-purple-300 space-y-1">
                  <div><strong>Solução 1 (Imediata):</strong> Clique no botão <em>"RODAR TESTE DE HARNESS DO VIGIA (SIMULAÇÃO GOVERNADA)"</em> acima para ver a verificação de escopo e o patch gerado.</div>
                  <div><strong>Solução 2 (Túnel Real):</strong> No seu terminal local, rode <code className="text-white bg-slate-950 px-1 py-0.5 rounded">npx localtunnel --port 11434</code> e cole a URL pública gerada no campo Endpoint.</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-3 font-mono text-xs">
              {executionResult.diagnostic && (
                <div className="rounded-lg bg-purple-950/40 border border-purple-800 p-3 text-purple-300 text-xs flex items-center space-x-2">
                  <Shield className="h-4 w-4 text-purple-400 shrink-0" />
                  <span>{executionResult.diagnostic}</span>
                </div>
              )}
              <div className="flex items-center space-x-4 text-slate-400">
                <span>Tokens Avaliados: <strong className="text-slate-200">{executionResult.prompt_tokens ?? 'N/A'}</strong></span>
                <span>Tokens Gerados: <strong className="text-purple-300">{executionResult.completion_tokens ?? 'N/A'}</strong></span>
                <span>Fidelidade de Escopo: <strong className="text-emerald-400">{executionResult.scope_adherent ? '100% ADERENTE' : 'VIOLADO'}</strong></span>
              </div>

              <div>
                <label className="text-slate-400 block mb-1">Patch / Código Gerado:</label>
                <div className="rounded-lg bg-slate-950 border border-slate-800 p-3 text-slate-300 font-mono text-[11px] whitespace-pre-wrap max-h-96 overflow-y-auto">
                  {executionResult.patch || executionResult.raw_response}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
