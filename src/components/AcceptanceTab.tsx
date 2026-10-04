import React, { useState, useEffect } from 'react';
import { ShieldCheck, Eye, EyeOff, RefreshCw, CheckCircle2, AlertOctagon, Info } from 'lucide-react';

interface AcceptanceResponse {
  decision: 'WOULD_ACCEPT' | 'WOULD_REJECT';
  status: 'NON_AUTHORITATIVE_PREVIEW';
  authority: 'NON_AUTHORITATIVE_PREVIEW';
  preview_only: true;
  reason: string;
  failures: string[];
  reviewed_at: string;
  acceptance_record: Record<string, any>;
}

export function AcceptanceTab() {
  const [useRawJson, setUseRawJson] = useState(false);

  // Form states
  const [classification, setClassification] = useState(() => localStorage.getItem('codepro_acc_classification') || 'M1_REAL_VERTICAL_VERIFIED');
  const [taskRef, setTaskRef] = useState(() => localStorage.getItem('codepro_acc_task_ref') || 'github://oigorbrito/codepro/issues/57');
  const [requestId, setRequestId] = useState(() => localStorage.getItem('codepro_acc_req_id') || 'm1-doctor-json-1');
  const [taskId, setTaskId] = useState(() => localStorage.getItem('codepro_acc_task_id') || 'issue-57-doctor-json');
  const [targetSha, setTargetSha] = useState(() => localStorage.getItem('codepro_acc_target_sha') || 'e401936979aea7f875508394aab1dac8f9e850d0');
  const [observedFiles, setObservedFiles] = useState(() => localStorage.getItem('codepro_acc_observed_files') || 'src/arkx/cli.py\ntests/test_cli.py');
  const [runId, setRunId] = useState(() => localStorage.getItem('codepro_acc_run_id') || 'run-m1-doctor-json-1-issue-57');
  const [runStatus, setRunStatus] = useState(() => localStorage.getItem('codepro_acc_run_status') || 'VERIFIED');

  // Raw JSON state
  const [rawPayload, setRawPayload] = useState(() => {
    return localStorage.getItem('codepro_acc_raw_payload') || '';
  });

  // Output
  const [result, setResult] = useState<AcceptanceResponse | null>(() => {
    const saved = localStorage.getItem('codepro_acc_result');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  // Sync state to local storage
  useEffect(() => {
    localStorage.setItem('codepro_acc_classification', classification);
    localStorage.setItem('codepro_acc_task_ref', taskRef);
    localStorage.setItem('codepro_acc_req_id', requestId);
    localStorage.setItem('codepro_acc_task_id', taskId);
    localStorage.setItem('codepro_acc_target_sha', targetSha);
    localStorage.setItem('codepro_acc_observed_files', observedFiles);
    localStorage.setItem('codepro_acc_run_id', runId);
    localStorage.setItem('codepro_acc_run_status', runStatus);
  }, [classification, taskRef, requestId, taskId, targetSha, observedFiles, runId, runStatus]);

  // Form compile helper
  const getCompiledPayload = () => {
    const filesArray = observedFiles
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);

    return {
      classification,
      task_ref: taskRef,
      request_id: requestId,
      task_id: taskId,
      target_base_sha: targetSha,
      provider_called: false,
      model_called: false,
      promotion: "NOT_AUTHORIZED",
      executor: {
        id: "local-command",
        selection: "EXPLICIT",
        fallback_allowed: false
      },
      observed_changed_files: filesArray,
      vertical_result: {
        run_id: runId,
        status: runStatus
      }
    };
  };

  // Compile to raw initially if empty
  useEffect(() => {
    if (!rawPayload) {
      setRawPayload(JSON.stringify(getCompiledPayload(), null, 2));
    }
  }, []);

  const handleReview = async () => {
    setLoading(true);
    setResult(null);

    let finalPayload: any;
    if (useRawJson) {
      try {
        finalPayload = JSON.parse(rawPayload);
        localStorage.setItem('codepro_acc_raw_payload', rawPayload);
      } catch (err) {
        alert('Invalid JSON in raw editor payload.');
        setLoading(false);
        return;
      }
    } else {
      finalPayload = getCompiledPayload();
      const compiledString = JSON.stringify(finalPayload, null, 2);
      setRawPayload(compiledString);
      localStorage.setItem('codepro_acc_raw_payload', compiledString);
    }

    try {
      const res = await fetch('/api/m1/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(finalPayload),
      });

      if (res.ok) {
        const json = await res.json();
        setResult(json);
        localStorage.setItem('codepro_acc_result', JSON.stringify(json));
      } else {
        const errJson = await res.json();
        alert(`Validation failed: ${errJson.error || 'Server error'}`);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <ShieldCheck className="h-5 w-5 text-indigo-400" />
          <span>M1 Acceptance Criteria Review (Preview)</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Preview local acceptance validations against the frozen M1 evidence rule set prior to committing and pushing telemetry.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Card: Evidence Builder */}
        <div className="lg:col-span-6 space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <div className="flex items-center justify-between pb-2 border-b border-slate-800/60">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold">
              Acceptance Form Builder
            </h3>
            
            <button
              onClick={() => {
                // If switching to raw, sync compiled form data first
                if (!useRawJson) {
                  setRawPayload(JSON.stringify(getCompiledPayload(), null, 2));
                }
                setUseRawJson(!useRawJson);
              }}
              className="text-xs font-mono text-indigo-400 hover:underline cursor-pointer"
            >
              {useRawJson ? 'Use Form Inputs' : 'Edit Raw JSON'}
            </button>
          </div>

          {!useRawJson ? (
            <div className="space-y-3.5">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Classification Type</label>
                <select
                  value={classification}
                  onChange={(e) => setClassification(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                >
                  <option value="M1_REAL_VERTICAL_VERIFIED">M1_REAL_VERTICAL_VERIFIED (Standard)</option>
                  <option value="M1_DRY_RUN_PREVIEW">M1_DRY_RUN_PREVIEW</option>
                  <option value="INVALID_CLASSIFICATION">INVALID_CLASSIFICATION (Test Negative)</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Issue/Task Ref</label>
                  <input
                    type="text"
                    value={taskRef}
                    onChange={(e) => setTaskRef(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Task ID</label>
                  <input
                    type="text"
                    value={taskId}
                    onChange={(e) => setTaskId(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Request ID</label>
                  <input
                    type="text"
                    value={requestId}
                    onChange={(e) => setRequestId(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Target Base SHA</label>
                  <input
                    type="text"
                    value={targetSha}
                    onChange={(e) => setTargetSha(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Observed Changed Files (One per line)</label>
                <textarea
                  rows={2.5}
                  value={observedFiles}
                  onChange={(e) => setObservedFiles(e.target.value)}
                  className="w-full rounded-lg bg-slate-950 border border-slate-800 p-2.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Vertical Run ID</label>
                  <input
                    type="text"
                    value={runId}
                    onChange={(e) => setRunId(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Run Status</label>
                  <select
                    value={runStatus}
                    onChange={(e) => setRunStatus(e.target.value)}
                    className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
                  >
                    <option value="VERIFIED">VERIFIED</option>
                    <option value="REJECTED">REJECTED</option>
                    <option value="FAILED">FAILED</option>
                  </select>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-300 mb-1">Raw Evidence Payload (JSON)</label>
              <textarea
                rows={12}
                value={rawPayload}
                onChange={(e) => setRawPayload(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 p-3 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
          )}

          <button
            onClick={handleReview}
            disabled={loading}
            className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 py-3 text-sm font-semibold uppercase tracking-wider text-white transition disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin" />
                <span>Validating acceptance...</span>
              </>
            ) : (
              <>
                <ShieldCheck className="h-4 w-4" />
                <span>Preview Acceptance Criteria</span>
              </>
            )}
          </button>
        </div>

        {/* Right Card: Outcome Decision */}
        <div className="lg:col-span-6 space-y-4">
          {result ? (
            <div className="space-y-4">
              {/* Decision outcome card */}
              <div
                className={`rounded-xl border p-5 ${
                  result.decision === 'WOULD_ACCEPT'
                    ? 'border-emerald-800/80 bg-emerald-950/20 text-emerald-300'
                    : 'border-rose-800/80 bg-rose-950/20 text-rose-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold uppercase tracking-wider text-slate-400">
                    Acceptance Criteria Decision
                  </span>
                  <span
                    className={`rounded-lg px-2.5 py-1 text-[10px] font-mono font-bold tracking-wider ${
                      result.decision === 'WOULD_ACCEPT'
                        ? 'bg-emerald-950 border border-emerald-800 text-emerald-400'
                        : 'bg-rose-950 border border-rose-800 text-rose-400'
                    }`}
                  >
                    {result.decision === 'WOULD_ACCEPT' ? 'ACCEPTED' : 'REJECTED'}
                  </span>
                </div>

                <div className="mt-3 text-sm font-medium text-slate-200">
                  {result.reason}
                </div>

                {result.failures && result.failures.length > 0 && (
                  <div className="mt-3 rounded-lg bg-rose-950/40 border border-rose-900/60 p-3 font-mono text-[11px] text-rose-300">
                    <strong className="block mb-1 font-bold">FAILURES ENFORCED ({result.failures.length}):</strong>
                    <ul className="list-disc list-inside space-y-0.5 pl-0.5">
                      {result.failures.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Acceptance record details */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-2">
                <div className="text-xs font-mono uppercase text-slate-400 font-bold mb-1">
                  Preview Evidence Record Log
                </div>
                <pre className="rounded-lg bg-slate-950 p-4 font-mono text-[11px] text-slate-400 overflow-x-auto border border-slate-800 leading-relaxed max-h-56">
                  {JSON.stringify(result.acceptance_record, null, 2)}
                </pre>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500 flex flex-col items-center justify-center h-full min-h-[300px]">
              <ShieldCheck className="h-10 w-10 text-slate-600 mb-3" />
              <p className="text-sm font-medium text-slate-400">Awaiting Acceptance Verification</p>
              <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
                Fill the form on the left or edit the JSON payload, then run the validation harness to check criteria conformity.
              </p>
            </div>
          )}

          {/* Quick Informational Tip */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 flex items-start space-x-3 text-xs text-slate-400">
            <Info className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-semibold text-slate-300">M1 Acceptance Policy:</span>
              <p className="leading-relaxed">
                Acceptance criteria are deterministic and verify compliance with frozen structures. This frontend acts as a non-authoritative tester to prevent malformed evidence submissions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
