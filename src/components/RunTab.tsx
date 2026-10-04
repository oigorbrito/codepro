import React, { useState, useEffect } from 'react';
import { PlayCircle, ChevronDown, ChevronUp, RefreshCw, FileText, CheckCircle2, AlertTriangle, Layers, Clock, Eye, EyeOff } from 'lucide-react';

interface TelemetryEvent {
  timestamp: string;
  type: string;
  run_id: string;
  data: Record<string, any>;
}

interface RunEvidence {
  run_id: string;
  status: string;
  reason: string;
  evidence_root: string;
  changed_files: string[];
  attempt_id: string;
  started_at: string;
  finished_at: string;
  duration_ms: number;
  events: TelemetryEvent[];
}

export function RunTab() {
  const [issues, setIssues] = useState<any[]>([]);
  const [selectedIssueNumber, setSelectedIssueNumber] = useState<number | ''>('');
  
  // Collapsible Advanced section state
  const [showAdvanced, setShowAdvanced] = useState(false);

  // States
  const [requestId, setRequestId] = useState(() => localStorage.getItem('codepro_run_request_id') || 'req-audit-v1');
  const [taskId, setTaskId] = useState(() => localStorage.getItem('codepro_run_task_id') || 'task-patch-verify-01');
  const [workspace, setWorkspace] = useState(() => localStorage.getItem('codepro_run_workspace') || '.');
  const [revision, setRevision] = useState(() => localStorage.getItem('codepro_run_revision') || 'e401936979aea7f875508394aab1dac8f9e850d0');
  const [requester, setRequester] = useState(() => localStorage.getItem('codepro_run_requester') || 'user://operator-1');
  const [authority, setAuthority] = useState(() => localStorage.getItem('codepro_run_authority') || 'grant://bounded-vertical-v1');
  const [acceptanceAuth, setAcceptanceAuth] = useState(() => localStorage.getItem('codepro_run_acceptance_auth') || 'acceptance://independent-pending');
  const [scope, setScope] = useState(() => localStorage.getItem('codepro_run_scope') || 'src/arkx/cli.py\ntests/test_cli.py');
  const [candidateFiles, setCandidateFiles] = useState(() => localStorage.getItem('codepro_run_candidate_files') || 'src/arkx/cli.py\ntests/test_cli.py');
  const [verifierArgv, setVerifierArgv] = useState(() => localStorage.getItem('codepro_run_verifier_argv') || '["npm", "test"]');
  const [executorArgv, setExecutorArgv] = useState(() => localStorage.getItem('codepro_run_executor_argv') || '["node", "-e", "console.log(\'verifying patch\')"]');

  // Outputs
  const [activeResult, setActiveResult] = useState<RunEvidence | null>(() => {
    const saved = localStorage.getItem('codepro_run_active_result');
    return saved ? JSON.parse(saved) : null;
  });
  const [evidenceList, setEvidenceList] = useState<RunEvidence[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch initial registry & history
  const fetchIssuesAndEvidence = async () => {
    try {
      const resIssues = await fetch('/api/codepro/issues');
      if (resIssues.ok) {
        const json = await resIssues.json();
        setIssues(json.issues || []);
      }
      const resEvidence = await fetch('/api/evidence');
      if (resEvidence.ok) {
        const list = await resEvidence.json();
        setEvidenceList(list);
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchIssuesAndEvidence();
  }, []);

  // Save state on change
  useEffect(() => {
    localStorage.setItem('codepro_run_request_id', requestId);
    localStorage.setItem('codepro_run_task_id', taskId);
    localStorage.setItem('codepro_run_workspace', workspace);
    localStorage.setItem('codepro_run_revision', revision);
    localStorage.setItem('codepro_run_requester', requester);
    localStorage.setItem('codepro_run_authority', authority);
    localStorage.setItem('codepro_run_acceptance_auth', acceptanceAuth);
    localStorage.setItem('codepro_run_scope', scope);
    localStorage.setItem('codepro_run_candidate_files', candidateFiles);
    localStorage.setItem('codepro_run_verifier_argv', verifierArgv);
    localStorage.setItem('codepro_run_executor_argv', executorArgv);
  }, [requestId, taskId, workspace, revision, requester, authority, acceptanceAuth, scope, candidateFiles, verifierArgv, executorArgv]);

  const handleSelectIssue = (num: number) => {
    setSelectedIssueNumber(num);
    const found = issues.find((i) => i.number === num);
    if (!found) return;

    setRequestId(`req-issue-${found.number}-${Date.now().toString(36)}`);
    setTaskId(`task-fix-issue-${found.number}`);
    setScope(found.scope.join('\n'));
    setCandidateFiles(found.candidate_files.join('\n'));
    // Auto preset verifier and executor matching the issue context
    setVerifierArgv(JSON.stringify(['npx', 'tsx', `tests/test_m2_m3_gates.ts`]));
    setExecutorArgv(JSON.stringify(['node', '-e', `console.log('simulating fix for issue #${found.number}')`]));
  };

  const handleRun = async () => {
    setLoading(true);
    setActiveResult(null);
    try {
      const scopeArray = scope
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const candidateArray = candidateFiles
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const verifierArray = JSON.parse(verifierArgv);
      const executorArray = JSON.parse(executorArgv);

      const payload = {
        workspace,
        revision,
        request_id: requestId,
        task_id: taskId,
        requester_ref: requester,
        authority_ref: authority,
        acceptance_authority_ref: acceptanceAuth,
        scope: scopeArray,
        candidate_files: candidateArray,
        affected_components: ['cli', 'core'],
        characterization_source_ref: 'codepro://p1/characterization-v1',
        max_wall_time_seconds: 300,
        attempt_id: 'attempt-1',
        executor_argv: executorArray,
        verifier_argv: verifierArray,
      };

      const res = await fetch('/api/vertical/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const json = await res.json();
        setActiveResult(json);
        localStorage.setItem('codepro_run_active_result', JSON.stringify(json));
        // Refresh evidence list
        fetchIssuesAndEvidence();
      }
    } catch (err) {
      console.error('Run failed', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <PlayCircle className="h-5 w-5 text-indigo-400" />
          <span>Minimal Operational Vertical Journey (codepro run)</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Select an issue to resolve and execute bounded code modifications within a governed, fail-closed runtime pipeline.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Configuration */}
        <div className="lg:col-span-6 space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold">
            Execution Configuration
          </h3>

          {/* User-Centered Quick Issue Selector */}
          <div className="space-y-1 bg-indigo-950/20 border border-indigo-900/40 p-4 rounded-xl">
            <label className="block text-xs font-bold text-indigo-300">
              Select Issue to Fix
            </label>
            <p className="text-[11px] text-slate-400 leading-normal">
              Pre-populates authorized files, scopes, tasks, and verifier inputs based on frozen standards.
            </p>
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
              className="mt-2 w-full rounded-lg bg-slate-950 px-3 py-2 text-xs font-mono text-indigo-200 border border-indigo-800/80 focus:border-indigo-500 focus:outline-none cursor-pointer"
            >
              <option value="">-- Choose a local repository issue --</option>
              {issues.map((issue) => (
                <option key={issue.number} value={issue.number}>
                  #{issue.number}: {issue.title}
                </option>
              ))}
            </select>
          </div>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Authorized Scope Boundaries
              </label>
              <p className="text-[11px] text-slate-500 mb-1 leading-normal font-mono">
                Only these paths may be modified. Violations reject modifications.
              </p>
              <textarea
                rows={2}
                value={scope}
                onChange={(e) => setScope(e.target.value)}
                placeholder="src/chassis/contracts.ts"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 font-mono text-xs text-emerald-400 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Attempted Candidate Files
              </label>
              <textarea
                rows={2}
                value={candidateFiles}
                onChange={(e) => setCandidateFiles(e.target.value)}
                placeholder="src/chassis/contracts.ts"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-2.5 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            {/* Collapsible Advanced Technical Section */}
            <div className="border-t border-slate-800/80 pt-3">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center space-x-1.5 text-xs text-indigo-400 hover:text-indigo-300 font-mono font-medium focus:outline-none cursor-pointer"
              >
                {showAdvanced ? (
                  <>
                    <ChevronUp className="h-3.5 w-3.5" />
                    <span>Hide low-level system variables</span>
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-3.5 w-3.5" />
                    <span>Show advanced environment configuration</span>
                  </>
                )}
              </button>

              {showAdvanced && (
                <div className="mt-4 space-y-3 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 text-xs space-y-3 font-mono">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-500">Request ID</label>
                      <input
                        type="text"
                        value={requestId}
                        onChange={(e) => setRequestId(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500">Task ID</label>
                      <input
                        type="text"
                        value={taskId}
                        onChange={(e) => setTaskId(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-500">Git Revision SHA</label>
                      <input
                        type="text"
                        value={revision}
                        onChange={(e) => setRevision(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500">Workspace root</label>
                      <input
                        type="text"
                        value={workspace}
                        onChange={(e) => setWorkspace(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-500">Requester ref</label>
                      <input
                        type="text"
                        value={requester}
                        onChange={(e) => setRequester(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500">Authority grant</label>
                      <input
                        type="text"
                        value={authority}
                        onChange={(e) => setAuthority(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500">Acceptance ref</label>
                      <input
                        type="text"
                        value={acceptanceAuth}
                        onChange={(e) => setAcceptanceAuth(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[10px] text-slate-500">Verifier argv JSON</label>
                      <input
                        type="text"
                        value={verifierArgv}
                        onChange={(e) => setVerifierArgv(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                    <div>
                      <label className="text-[10px] text-slate-500">Executor argv JSON</label>
                      <input
                        type="text"
                        value={executorArgv}
                        onChange={(e) => setExecutorArgv(e.target.value)}
                        className="w-full rounded border border-slate-800 bg-slate-900 px-2 py-1 text-slate-300"
                      />
                    </div>
                  </div>
                </div>
              )}
            </div>

            <button
              onClick={handleRun}
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 py-3 text-sm font-semibold uppercase tracking-wider text-white transition disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Executing governed journey...</span>
                </>
              ) : (
                <>
                  <PlayCircle className="h-4 w-4" />
                  <span>Execute Governed Run</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Execution Outcome & Logs */}
        <div className="lg:col-span-6 space-y-4">
          {activeResult ? (
            <div className="space-y-4">
              {/* Outcome Status Banner */}
              <div
                className={`rounded-xl border p-5 ${
                  activeResult.status === 'VERIFIED'
                    ? 'border-emerald-800/80 bg-emerald-950/20 text-emerald-300'
                    : 'border-rose-800/80 bg-rose-950/20 text-rose-300'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold flex items-center space-x-1.5 uppercase">
                    <Layers className="h-3.5 w-3.5 text-indigo-400" />
                    <span>Outcome Classification</span>
                  </span>
                  <span className="font-mono text-xs tabular-nums text-slate-400 flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>{activeResult.duration_ms}ms</span>
                  </span>
                </div>

                <div className="mt-3 text-lg font-bold tracking-tight text-white flex items-center space-x-2">
                  <span className={activeResult.status === 'VERIFIED' ? 'text-emerald-400' : 'text-rose-400'}>
                    {activeResult.status}
                  </span>
                </div>
                <p className="text-xs mt-1 text-slate-300 leading-normal">{activeResult.reason}</p>
                
                <div className="text-[10px] font-mono text-slate-500 mt-3 pt-3 border-t border-slate-800/35">
                  Evidence Root: {activeResult.evidence_root} · Changed: {activeResult.changed_files.join(', ') || 'none'}
                </div>
              </div>

              {/* Telemetry Log Stream */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
                <h4 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                  Recorded Telemetry Events ({activeResult.events.length})
                </h4>

                <div className="space-y-2.5 max-h-64 overflow-y-auto pr-1">
                  {activeResult.events.map((evt, idx) => (
                    <div
                      key={idx}
                      className="rounded-lg bg-slate-950/90 border border-slate-800/80 p-3 font-mono text-[11px]"
                    >
                      <div className="flex items-center justify-between text-indigo-400">
                        <span className="font-semibold">{evt.type}</span>
                        <span className="text-slate-500 text-[10px] tabular-nums">
                          {new Date(evt.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <pre className="mt-1.5 text-[10px] text-slate-400 overflow-x-auto leading-relaxed max-h-24">
                        {JSON.stringify(evt.data, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500 flex flex-col items-center justify-center h-full min-h-[300px]">
              <FileText className="h-10 w-10 text-slate-600 mb-3" />
              <p className="text-sm font-medium text-slate-400">No active execution</p>
              <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
                Select an issue and click "Execute Governed Run" to monitor the real-time event telemetry stream.
              </p>
            </div>
          )}

          {/* Historical Persisted Runs */}
          {evidenceList.length > 0 && (
            <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 space-y-2">
              <div className="text-xs font-mono uppercase text-slate-400 font-semibold">
                Historical Evidence Store ({evidenceList.length})
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto pr-1">
                {evidenceList.map((run) => (
                  <div
                    key={run.run_id}
                    onClick={() => {
                      setActiveResult(run);
                      localStorage.setItem('codepro_run_active_result', JSON.stringify(run));
                    }}
                    className="flex items-center justify-between rounded-lg p-2.5 text-xs font-mono bg-slate-950 hover:bg-slate-800 cursor-pointer border border-slate-800/80 transition"
                  >
                    <span className="truncate w-36 text-slate-400">{run.run_id}</span>
                    <span
                      className={`text-[10px] font-bold ${
                        run.status === 'VERIFIED' ? 'text-emerald-400' : 'text-rose-400'
                      }`}
                    >
                      {run.status}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
