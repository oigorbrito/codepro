import React, { useState, useEffect } from 'react';
import {
  Activity,
  Terminal,
  Search,
  Cpu,
  PlayCircle,
  FileCheck,
  ShieldCheck,
  FolderGit2,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  FileText,
  Clock,
  Layers,
  ChevronRight,
  Database,
  Sliders,
  Copy,
  Check,
} from 'lucide-react';

interface DoctorCheck {
  name: string;
  label: string;
  ok: boolean;
  detail: string;
  required?: string;
}

interface DoctorResponse {
  status: 'PASS' | 'FAIL';
  timestamp: string;
  checks: DoctorCheck[];
}

interface InspectionResponse {
  project_name: string;
  project_root: string;
  git_available: boolean;
  git_repository: boolean;
  branch: string | null;
  languages: string[];
  test_surfaces: string[];
  executors: Array<{ name: string; command: string; available: boolean }>;
  timestamp: string;
}

interface CharacterizationResponse {
  scope: string;
  recommended_path: string;
  confidence: string;
  reason_codes: string[];
  reasons: string[];
  characterized_at: string;
}

interface RoutingResponse {
  decision: string;
  action: string;
  selected_path: string;
  target_executor_tier: string;
  reasons: string[];
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
  events: Array<{
    timestamp: string;
    type: string;
    run_id: string;
    data: Record<string, unknown>;
  }>;
}

interface AcceptanceResponse {
  decision: 'ACCEPTED' | 'REJECTED';
  status: string;
  reason: string;
  failures: string[];
  reviewed_at: string;
  acceptance_record: Record<string, unknown>;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<'doctor' | 'inspect' | 'characterize' | 'run' | 'acceptance' | 'decision-basis' | 'fixtures'>('doctor');

  // Doctor state
  const [doctorData, setDoctorData] = useState<DoctorResponse | null>(null);
  const [doctorLoading, setDoctorLoading] = useState(false);

  // Inspect state
  const [inspectPath, setInspectPath] = useState('.');
  const [inspectData, setInspectData] = useState<InspectionResponse | null>(null);
  const [inspectLoading, setInspectLoading] = useState(false);

  // Characterize state
  const [candidateFiles, setCandidateFiles] = useState('src/arkx/cli.py\ntests/test_cli.py');
  const [affectedComponents, setAffectedComponents] = useState('cli, chassis');
  const [ambiguityMarkers, setAmbiguityMarkers] = useState('');
  const [riskMarkers, setRiskMarkers] = useState('');
  const [archChange, setArchChange] = useState(false);
  const [sharedState, setSharedState] = useState(false);
  const [charResult, setCharResult] = useState<CharacterizationResponse | null>(null);
  const [routingResult, setRoutingResult] = useState<RoutingResponse | null>(null);
  const [charLoading, setCharLoading] = useState(false);

  // Vertical Run state
  const [runRequestId, setRunRequestId] = useState('req-audit-v1');
  const [runTaskId, setRunTaskId] = useState('task-patch-verify-01');
  const [runWorkspace, setRunWorkspace] = useState('.');
  const [runRevision, setRunRevision] = useState('e401936979aea7f875508394aab1dac8f9e850d0');
  const [runRequester, setRunRequester] = useState('user://operator-1');
  const [runAuthority, setRunAuthority] = useState('grant://bounded-vertical-v1');
  const [runAcceptanceAuth, setRunAcceptanceAuth] = useState('acceptance://independent-pending');
  const [runScope, setRunScope] = useState('src/arkx/cli.py\ntests/test_cli.py');
  const [runCandidateFiles, setRunCandidateFiles] = useState('src/arkx/cli.py\ntests/test_cli.py');
  const [runVerifierArgv, setRunVerifierArgv] = useState('["npm", "test"]');
  const [runExecutorArgv, setRunExecutorArgv] = useState('["node", "-e", "console.log(\'verifying patch\')"]');
  const [activeRunResult, setActiveRunResult] = useState<RunEvidence | null>(null);
  const [runLoading, setRunLoading] = useState(false);
  const [evidenceList, setEvidenceList] = useState<RunEvidence[]>([]);

  // Acceptance state
  const [m1Payload, setM1Payload] = useState(JSON.stringify({
    classification: "M1_REAL_VERTICAL_VERIFIED",
    task_ref: "github://oigorbrito/codepro/issues/57",
    request_id: "m1-doctor-json-1",
    task_id: "issue-57-doctor-json",
    target_base_sha: "e401936979aea7f875508394aab1dac8f9e850d0",
    provider_called: false,
    model_called: false,
    promotion: "NOT_AUTHORIZED",
    executor: {
      id: "local-command",
      selection: "EXPLICIT",
      fallback_allowed: false
    },
    observed_changed_files: [
      "src/arkx/cli.py",
      "tests/test_cli.py"
    ],
    vertical_result: {
      run_id: "run-m1-doctor-json-1-issue-57",
      status: "VERIFIED"
    }
  }, null, 2));
  const [acceptanceResult, setAcceptanceResult] = useState<AcceptanceResponse | null>(null);
  const [acceptanceLoading, setAcceptanceLoading] = useState(false);

  // Decision Basis state
  const [basisProblemClass, setBasisProblemClass] = useState('runtime_chassis_migration');
  const [basisDecision, setBasisDecision] = useState('migrate to Node.js 22 full-stack Express + Vite React SPA');
  const [basisType, setBasisType] = useState('OFFICIAL_DOC');
  const [basisRef, setBasisRef] = useState('/skills/system_skills/github_import_migration/references/web.md');
  const [basisClaim, setBasisClaim] = useState('Python repositories converted to Node.js web services with port 3000 entry point');
  const [basisApplicability, setBasisApplicability] = useState('AI Studio web environment constraints require port 3000 Node.js dev server');
  const [basisDeviation, setBasisDeviation] = useState('none');
  const [basisOutput, setBasisOutput] = useState('');
  const [copiedBasis, setCopiedBasis] = useState(false);

  // Fixtures state
  const [fixtures, setFixtures] = useState<Record<string, { name: string; type: string; description: string; data: unknown }>>({});
  const [selectedFixtureKey, setSelectedFixtureKey] = useState<string>('');

  // Initial fetch
  useEffect(() => {
    fetchDoctor();
    fetchEvidence();
    fetchFixtures();
  }, []);

  const fetchDoctor = async () => {
    setDoctorLoading(true);
    try {
      const res = await fetch('/api/doctor');
      const data = await res.json();
      setDoctorData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setDoctorLoading(false);
    }
  };

  const handleInspect = async () => {
    setInspectLoading(true);
    try {
      const res = await fetch('/api/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: inspectPath }),
      });
      const data = await res.json();
      setInspectData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setInspectLoading(false);
    }
  };

  const handleCharacterizeAndRoute = async () => {
    setCharLoading(true);
    try {
      const candidates = candidateFiles
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const components = affectedComponents
        .split(',')
        .map((s) => s.trim())
        .filter(Boolean);
      const ambiguities = ambiguityMarkers
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const risks = riskMarkers
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);

      const signals = {
        candidate_files: candidates.length > 0 ? candidates : null,
        affected_components: components,
        ambiguity_markers: ambiguities,
        risk_markers: risks,
        architectural_change: archChange,
        state_shared: sharedState,
      };

      const charRes = await fetch('/api/characterize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signals }),
      });
      const charJson: CharacterizationResponse = await charRes.json();
      setCharResult(charJson);

      // Route
      const routeRes = await fetch('/api/routing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          characterization: charJson,
          escalation_budget: 2,
          current_escalation_level: 0,
        }),
      });
      const routeJson: RoutingResponse = await routeRes.json();
      setRoutingResult(routeJson);
    } catch (err) {
      console.error(err);
    } finally {
      setCharLoading(false);
    }
  };

  const handleRunVertical = async () => {
    setRunLoading(true);
    try {
      const scopeArray = runScope
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const candidateArray = runCandidateFiles
        .split('\n')
        .map((s) => s.trim())
        .filter(Boolean);
      const verifierArray = JSON.parse(runVerifierArgv);
      const executorArray = JSON.parse(runExecutorArgv);

      const payload = {
        workspace: runWorkspace,
        revision: runRevision,
        request_id: runRequestId,
        task_id: runTaskId,
        requester_ref: runRequester,
        authority_ref: runAuthority,
        acceptance_authority_ref: runAcceptanceAuth,
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
      const data = await res.json();
      setActiveRunResult(data);
      fetchEvidence();
    } catch (err) {
      console.error(err);
    } finally {
      setRunLoading(false);
    }
  };

  const fetchEvidence = async () => {
    try {
      const res = await fetch('/api/evidence');
      const data = await res.json();
      setEvidenceList(data);
    } catch (err) {
      console.error(err);
    }
  };

  const handleReviewAcceptance = async () => {
    setAcceptanceLoading(true);
    try {
      const payload = JSON.parse(m1Payload);
      const res = await fetch('/api/m1/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      setAcceptanceResult(data);
    } catch (err) {
      alert('Invalid JSON in M1 Evidence payload');
      console.error(err);
    } finally {
      setAcceptanceLoading(false);
    }
  };

  const handleGenerateDecisionBasis = async () => {
    try {
      const res = await fetch('/api/decision-basis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_class: basisProblemClass,
          decision: basisDecision,
          basis_type: basisType,
          basis_ref: basisRef,
          supported_claim: basisClaim,
          applicability: basisApplicability,
          deviation: basisDeviation,
        }),
      });
      const data = await res.json();
      if (data.formatted) {
        setBasisOutput(data.formatted);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const fetchFixtures = async () => {
    try {
      const res = await fetch('/api/fixtures');
      const data = await res.json();
      setFixtures(data);
      const keys = Object.keys(data);
      if (keys.length > 0) {
        setSelectedFixtureKey(keys[0]);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadPresetSignals = (preset: 'simple' | 'localized' | 'repo' | 'ambiguous') => {
    if (preset === 'simple') {
      setCandidateFiles('src/arkx/contracts.ts');
      setAffectedComponents('contracts');
      setAmbiguityMarkers('');
      setRiskMarkers('');
      setArchChange(false);
      setSharedState(false);
    } else if (preset === 'localized') {
      setCandidateFiles('src/arkx/telemetry.ts\ntests/test_telemetry.ts');
      setAffectedComponents('telemetry, contracts');
      setAmbiguityMarkers('');
      setRiskMarkers('');
      setArchChange(false);
      setSharedState(false);
    } else if (preset === 'repo') {
      setCandidateFiles('src/arkx/a.ts\nsrc/arkx/b.ts\nsrc/arkx/c.ts\ntests/test_a.ts\ntests/test_b.ts\ndocs/architecture.md');
      setAffectedComponents('runtime, storage, api');
      setAmbiguityMarkers('');
      setRiskMarkers('cross-module mutation');
      setArchChange(true);
      setSharedState(true);
    } else if (preset === 'ambiguous') {
      setCandidateFiles('');
      setAffectedComponents('unknown');
      setAmbiguityMarkers('acceptance unclear\nunbounded specification');
      setRiskMarkers('');
      setArchChange(false);
      setSharedState(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedBasis(true);
    setTimeout(() => setCopiedBasis(false), 2000);
  };

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100 font-sans antialiased overflow-hidden">
      {/* Top Header */}
      <header className="flex h-16 items-center justify-between border-b border-slate-800 bg-slate-900/90 px-6 backdrop-blur">
        <div className="flex items-center space-x-4">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-blue-600 font-mono text-xl font-bold text-white shadow-md shadow-blue-500/20">
            CP
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold tracking-tight text-white">CodePro Chassis</h1>
              <span className="rounded bg-blue-900/50 px-2 py-0.5 font-mono text-xs text-blue-300 border border-blue-700/50">
                v0.3.0
              </span>
              <span className="rounded bg-emerald-950 px-2 py-0.5 font-mono text-xs text-emerald-400 border border-emerald-800">
                FAIL-CLOSED TELEMETRY
              </span>
            </div>
            <p className="text-xs text-slate-400 font-mono">
              MINIMUM SUFFICIENT ARCHITECTURE FOR MAXIMUM RELIABLE CAPABILITY
            </p>
          </div>
        </div>

        {/* Chassis status banner */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 rounded-lg bg-slate-800/80 px-3 py-1.5 border border-slate-700">
            <Activity className="h-4 w-4 text-emerald-400 animate-pulse" />
            <span className="text-xs font-mono text-slate-300">
              Fingerprint: <strong className="text-slate-100">v0.3.0-deterministic</strong>
            </span>
          </div>
          <button
            onClick={fetchDoctor}
            className="flex items-center space-x-1.5 rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-300 hover:bg-slate-700 hover:text-white transition border border-slate-700"
            title="Refresh Diagnostics"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${doctorLoading ? 'animate-spin' : ''}`} />
            <span>Doctor</span>
          </button>
        </div>
      </header>

      {/* Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Nav */}
        <aside className="w-64 border-r border-slate-800 bg-slate-900/60 p-4 flex flex-col justify-between">
          <nav className="space-y-1">
            <button
              onClick={() => setActiveTab('doctor')}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'doctor'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Activity className="h-4 w-4" />
              <span>Chassis Doctor</span>
            </button>

            <button
              onClick={() => {
                setActiveTab('inspect');
                if (!inspectData) handleInspect();
              }}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'inspect'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Search className="h-4 w-4" />
              <span>Project Inspect</span>
            </button>

            <button
              onClick={() => setActiveTab('characterize')}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'characterize'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Sliders className="h-4 w-4" />
              <span>P1 Characterization</span>
            </button>

            <button
              onClick={() => setActiveTab('run')}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'run'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <PlayCircle className="h-4 w-4" />
              <span>Vertical Run (P0/P5)</span>
            </button>

            <button
              onClick={() => setActiveTab('acceptance')}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'acceptance'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <ShieldCheck className="h-4 w-4" />
              <span>M1 Acceptance</span>
            </button>

            <button
              onClick={() => setActiveTab('decision-basis')}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'decision-basis'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <FileCheck className="h-4 w-4" />
              <span>AGENTS.md Policy</span>
            </button>

            <button
              onClick={() => setActiveTab('fixtures')}
              className={`flex w-full items-center space-x-3 rounded-lg px-3 py-2.5 text-sm font-medium transition ${
                activeTab === 'fixtures'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              <Database className="h-4 w-4" />
              <span>Fixtures Explorer</span>
            </button>
          </nav>

          <div className="rounded-lg bg-slate-950/60 p-3 border border-slate-800/80 font-mono text-[11px] text-slate-400 space-y-1">
            <div className="text-slate-300 font-semibold mb-1">CONTRACT GUARANTEE</div>
            <div>• NO_SILENT_FALLBACK</div>
            <div>• NO_SILENT_SWITCH</div>
            <div>• EXPLICIT_BOUNDS</div>
            <div>• VERIFIED != ACCEPTED</div>
          </div>
        </aside>

        {/* Workspace Area */}
        <main className="flex-1 overflow-y-auto p-6 bg-slate-950">
          {/* TAB 1: DOCTOR */}
          {activeTab === 'doctor' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-blue-400" />
                  <span>Chassis Doctor & Runtime Environment</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Verifies local runtime execution boundaries, contract schema integrity, and executor environments without running task jobs.
                </p>
              </div>

              {doctorData ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-xl bg-slate-900 border border-slate-800 p-4">
                    <div className="flex items-center space-x-3">
                      {doctorData.status === 'PASS' ? (
                        <CheckCircle2 className="h-6 w-6 text-emerald-400" />
                      ) : (
                        <AlertTriangle className="h-6 w-6 text-amber-400" />
                      )}
                      <div>
                        <div className="text-base font-semibold text-white">
                          Chassis Diagnostic: {doctorData.status}
                        </div>
                        <div className="text-xs text-slate-400 font-mono">
                          Evaluated at: {new Date(doctorData.timestamp).toLocaleTimeString()}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={fetchDoctor}
                      className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-700 transition"
                    >
                      Re-run Checks
                    </button>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {doctorData.checks.map((check) => (
                      <div
                        key={check.name}
                        className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 flex items-start justify-between"
                      >
                        <div className="space-y-1">
                          <div className="text-sm font-medium text-slate-200">{check.label}</div>
                          <div className="text-xs font-mono text-slate-400">
                            Status: <span className="text-slate-100 font-bold">{check.detail}</span>
                          </div>
                          {check.required && (
                            <div className="text-[11px] text-slate-500 font-mono">
                              Required: {check.required}
                            </div>
                          )}
                        </div>
                        <span
                          className={`rounded px-2 py-0.5 text-xs font-mono font-semibold ${
                            check.ok
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : 'bg-amber-950 text-amber-400 border border-amber-800'
                          }`}
                        >
                          {check.ok ? 'PASS' : 'WARN'}
                        </span>
                      </div>
                    ))}
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                    <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2 font-semibold">
                      Chassis Invariants & Policies
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs text-slate-300">
                      <div className="rounded bg-slate-950/80 p-3 border border-slate-800">
                        <strong className="text-blue-400 block mb-1">P0 Execution Telemetry</strong>
                        Fail-closed serializable event stream with strict ISO-8601 timestamps and non-empty run IDs.
                      </div>
                      <div className="rounded bg-slate-950/80 p-3 border border-slate-800">
                        <strong className="text-blue-400 block mb-1">P1 Characterization</strong>
                        Deterministic, conservative scope classification without NLP inference or speculative jumps.
                      </div>
                      <div className="rounded bg-slate-950/80 p-3 border border-slate-800">
                        <strong className="text-blue-400 block mb-1">P3 Routing & Escalation</strong>
                        Rule-based routing refusing hidden fallback or silent executor switches.
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-8 text-center text-slate-500 font-mono text-sm">
                  Loading diagnostics...
                </div>
              )}
            </div>
          )}

          {/* TAB 2: INSPECT */}
          {activeTab === 'inspect' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Search className="h-5 w-5 text-blue-400" />
                  <span>Project Inspection (codepro inspect)</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Read-only local project inspection. Queries Git context, test surfaces, markers, and known executor binaries in PATH.
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <input
                  type="text"
                  value={inspectPath}
                  onChange={(e) => setInspectPath(e.target.value)}
                  placeholder="Target directory path (e.g. .)"
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3.5 py-2 font-mono text-sm text-slate-100 placeholder-slate-500 focus:border-blue-500 focus:outline-none"
                />
                <button
                  onClick={handleInspect}
                  disabled={inspectLoading}
                  className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-500 disabled:opacity-50 transition"
                >
                  {inspectLoading ? 'Inspecting...' : 'Inspect Project'}
                </button>
              </div>

              {inspectData && (
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                      <div className="text-xs font-mono uppercase text-slate-400">Workspace Context</div>
                      <div className="text-sm">
                        <span className="text-slate-400">Project Name: </span>
                        <strong className="text-white">{inspectData.project_name}</strong>
                      </div>
                      <div className="text-sm font-mono text-xs truncate">
                        <span className="text-slate-400">Root: </span>
                        <span className="text-slate-300">{inspectData.project_root}</span>
                      </div>
                      <div className="text-sm">
                        <span className="text-slate-400">Git Available: </span>
                        <strong className={inspectData.git_available ? 'text-emerald-400' : 'text-rose-400'}>
                          {inspectData.git_available ? 'Yes' : 'No'}
                        </strong>
                      </div>
                      <div className="text-sm">
                        <span className="text-slate-400">Git Repo: </span>
                        <strong className={inspectData.git_repository ? 'text-emerald-400' : 'text-rose-400'}>
                          {inspectData.git_repository ? 'Yes' : 'No'}
                        </strong>
                      </div>
                      <div className="text-sm font-mono text-xs">
                        <span className="text-slate-400">Branch: </span>
                        <span className="text-blue-400">{inspectData.branch || 'None'}</span>
                      </div>
                    </div>

                    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                      <div>
                        <div className="text-xs font-mono uppercase text-slate-400 mb-1">Detected Languages</div>
                        <div className="flex flex-wrap gap-1.5">
                          {inspectData.languages.length > 0 ? (
                            inspectData.languages.map((lang) => (
                              <span
                                key={lang}
                                className="rounded bg-slate-800 border border-slate-700 px-2 py-0.5 text-xs font-medium text-slate-200"
                              >
                                {lang}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500 font-mono">None detected</span>
                          )}
                        </div>
                      </div>

                      <div>
                        <div className="text-xs font-mono uppercase text-slate-400 mb-1">Test Surfaces</div>
                        <div className="flex flex-wrap gap-1.5">
                          {inspectData.test_surfaces.length > 0 ? (
                            inspectData.test_surfaces.map((s) => (
                              <span
                                key={s}
                                className="rounded bg-emerald-950 border border-emerald-800 px-2 py-0.5 text-xs font-medium text-emerald-300"
                              >
                                {s}/
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500 font-mono">None detected</span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Executors */}
                  <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                    <div className="text-xs font-mono uppercase text-slate-400 mb-3 font-semibold">
                      Coding Executor Binaries in Host PATH
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                      {inspectData.executors.map((exec) => (
                        <div
                          key={exec.name}
                          className="rounded-lg border border-slate-800 bg-slate-950 p-3 flex items-center justify-between"
                        >
                          <div>
                            <div className="text-xs font-bold text-slate-200">{exec.name}</div>
                            <div className="text-[11px] font-mono text-slate-500">{exec.command}</div>
                          </div>
                          <span
                            className={`rounded px-1.5 py-0.5 text-[10px] font-mono font-semibold ${
                              exec.available
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                : 'bg-slate-800 text-slate-400'
                            }`}
                          >
                            {exec.available ? 'AVAILABLE' : 'ABSENT'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 3: CHARACTERIZE & ROUTING */}
          {activeTab === 'characterize' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Sliders className="h-5 w-5 text-blue-400" />
                  <span>Task Characterization & Routing (P1 - P3)</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Deterministic task characterization evaluating candidate files, component blast radius, and ambiguity signals into bounded routing policies.
                </p>
              </div>

              {/* Preset buttons */}
              <div className="flex items-center space-x-2">
                <span className="text-xs font-mono text-slate-400 mr-2">Load Synthetic Fixture:</span>
                <button
                  onClick={() => loadPresetSignals('simple')}
                  className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 hover:bg-slate-700 border border-slate-700"
                >
                  Simple (Single-File)
                </button>
                <button
                  onClick={() => loadPresetSignals('localized')}
                  className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 hover:bg-slate-700 border border-slate-700"
                >
                  Localized (Bounded Set)
                </button>
                <button
                  onClick={() => loadPresetSignals('repo')}
                  className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 hover:bg-slate-700 border border-slate-700"
                >
                  Repository-Wide
                </button>
                <button
                  onClick={() => loadPresetSignals('ambiguous')}
                  className="rounded bg-slate-800 px-2.5 py-1 text-xs font-mono text-slate-300 hover:bg-slate-700 border border-slate-700"
                >
                  Ambiguous (Qualification Req)
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
                    Explicit Signal Inputs
                  </h3>

                  <div>
                    <label className="text-xs font-mono text-slate-400 block mb-1">
                      Candidate Files (one per line):
                    </label>
                    <textarea
                      rows={3}
                      value={candidateFiles}
                      onChange={(e) => setCandidateFiles(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-mono text-slate-400 block mb-1">
                      Affected Components (comma-separated):
                    </label>
                    <input
                      type="text"
                      value={affectedComponents}
                      onChange={(e) => setAffectedComponents(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="text-xs font-mono text-slate-400 block mb-1">
                      Ambiguity Markers (triggers fail-closed qualification):
                    </label>
                    <input
                      type="text"
                      value={ambiguityMarkers}
                      onChange={(e) => setAmbiguityMarkers(e.target.value)}
                      placeholder="e.g. acceptance unclear"
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200 focus:border-blue-500 focus:outline-none"
                    />
                  </div>

                  <div className="flex items-center space-x-4 pt-1">
                    <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={archChange}
                        onChange={(e) => setArchChange(e.target.checked)}
                        className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
                      />
                      <span>Architectural Change</span>
                    </label>
                    <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={sharedState}
                        onChange={(e) => setSharedState(e.target.checked)}
                        className="rounded border-slate-700 bg-slate-900 text-blue-600 focus:ring-0"
                      />
                      <span>Shared State Mutated</span>
                    </label>
                  </div>

                  <button
                    onClick={handleCharacterizeAndRoute}
                    disabled={charLoading}
                    className="w-full rounded bg-blue-600 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-blue-500 disabled:opacity-50 transition"
                  >
                    {charLoading ? 'Evaluating...' : 'Evaluate Characterization & Routing'}
                  </button>
                </div>

                {/* Outputs */}
                <div className="space-y-4">
                  {charResult ? (
                    <div className="space-y-4">
                      {/* Characterization Result Card */}
                      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-slate-400">P1 Characterization</span>
                          <span className="rounded bg-blue-950 text-blue-300 border border-blue-800 px-2 py-0.5 font-mono text-xs font-bold">
                            {charResult.scope}
                          </span>
                        </div>
                        <div className="text-xs font-mono">
                          <span className="text-slate-400">Recommended Path: </span>
                          <strong className="text-white">{charResult.recommended_path}</strong>
                        </div>
                        <div className="text-xs font-mono">
                          <span className="text-slate-400">Confidence: </span>
                          <strong className="text-emerald-400">{charResult.confidence}</strong>
                        </div>
                        <div className="text-xs font-mono text-slate-400">
                          Reasons:
                          <ul className="list-disc list-inside mt-1 text-slate-300 space-y-0.5">
                            {charResult.reasons.map((r, i) => (
                              <li key={i}>{r}</li>
                            ))}
                          </ul>
                        </div>
                      </div>

                      {/* Routing Result Card */}
                      {routingResult && (
                        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-mono uppercase text-slate-400">P3 Routing Decision</span>
                            <span className="rounded bg-emerald-950 text-emerald-400 border border-emerald-800 px-2 py-0.5 font-mono text-xs font-bold">
                              {routingResult.decision}
                            </span>
                          </div>
                          <div className="text-xs font-mono">
                            <span className="text-slate-400">Escalation Action: </span>
                            <strong className="text-white">{routingResult.action}</strong>
                          </div>
                          <div className="text-xs font-mono">
                            <span className="text-slate-400">Target Executor Tier: </span>
                            <strong className="text-blue-400">{routingResult.target_executor_tier}</strong>
                          </div>
                          <div className="text-xs font-mono text-slate-400">
                            Policy Basis:
                            <ul className="list-disc list-inside mt-1 text-slate-300 space-y-0.5">
                              {routingResult.reasons.map((r, i) => (
                                <li key={i}>{r}</li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs font-mono text-slate-500">
                      Configure signals on the left and click Evaluate to see deterministic classification.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 4: VERTICAL RUN */}
          {activeTab === 'run' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <PlayCircle className="h-5 w-5 text-blue-400" />
                  <span>Minimal Operational Vertical Journey (codepro run)</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Executes one explicit, bounded command against one exact clean Git revision. Strictly enforces authorized scope boundary and produces structured non-overwriting audit evidence.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Run parameters form */}
                <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="text-xs font-mono uppercase text-slate-400 font-semibold mb-2">
                    Explicit Authority & Scope Boundaries
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="text-[11px] font-mono text-slate-400">Request ID</label>
                      <input
                        type="text"
                        value={runRequestId}
                        onChange={(e) => setRunRequestId(e.target.value)}
                        className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-100"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-mono text-slate-400">Task ID</label>
                      <input
                        type="text"
                        value={runTaskId}
                        onChange={(e) => setRunTaskId(e.target.value)}
                        className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-100"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">Exact Revision SHA</label>
                    <input
                      type="text"
                      value={runRevision}
                      onChange={(e) => setRunRevision(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-100"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">
                      Authorized Scope (one file per line)
                    </label>
                    <textarea
                      rows={2}
                      value={runScope}
                      onChange={(e) => setRunScope(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-100"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">
                      Candidate Files Attempted (must be subset of scope)
                    </label>
                    <textarea
                      rows={2}
                      value={runCandidateFiles}
                      onChange={(e) => setRunCandidateFiles(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 p-2 font-mono text-xs text-slate-100"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">Verifier argv JSON</label>
                    <input
                      type="text"
                      value={runVerifierArgv}
                      onChange={(e) => setRunVerifierArgv(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1 font-mono text-xs text-slate-100"
                    />
                  </div>

                  <button
                    onClick={handleRunVertical}
                    disabled={runLoading}
                    className="w-full rounded bg-blue-600 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-blue-500 disabled:opacity-50 transition"
                  >
                    {runLoading ? 'Executing Governed Journey...' : 'Run Governed Journey'}
                  </button>
                </div>

                {/* Live Run Evidence & Telemetry */}
                <div className="space-y-4">
                  {activeRunResult ? (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-slate-400">Execution Result</span>
                          <span
                            className={`rounded px-2 py-0.5 font-mono text-xs font-bold border ${
                              activeRunResult.status === 'VERIFIED'
                                ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                                : 'bg-rose-950 text-rose-400 border-rose-800'
                            }`}
                          >
                            {activeRunResult.status}
                          </span>
                        </div>
                        <div className="text-xs font-mono text-slate-300">
                          <strong>Run ID: </strong>
                          <span className="text-blue-400">{activeRunResult.run_id}</span>
                        </div>
                        <div className="text-xs font-mono text-slate-400">
                          Reason: <span className="text-slate-200">{activeRunResult.reason}</span>
                        </div>
                        <div className="text-xs font-mono text-slate-400">
                          Changed Files: {activeRunResult.changed_files.join(', ') || 'none'}
                        </div>
                      </div>

                      {/* Telemetry Stream */}
                      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <div className="text-xs font-mono uppercase text-slate-400 mb-2 font-semibold">
                          Recorded Telemetry Events ({activeRunResult.events.length})
                        </div>
                        <div className="space-y-2 max-h-64 overflow-y-auto font-mono text-[11px]">
                          {activeRunResult.events.map((evt, idx) => (
                            <div key={idx} className="rounded bg-slate-950 p-2 border border-slate-800/80">
                              <div className="flex items-center justify-between text-blue-400">
                                <span>{evt.type}</span>
                                <span className="text-slate-500">
                                  {new Date(evt.timestamp).toLocaleTimeString()}
                                </span>
                              </div>
                              <pre className="mt-1 text-[10px] text-slate-300 overflow-x-auto">
                                {JSON.stringify(evt.data, null, 2)}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs font-mono text-slate-500">
                      Configure run parameters and execute to observe telemetry event stream.
                    </div>
                  )}

                  {/* Historical Runs */}
                  {evidenceList.length > 0 && (
                    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4">
                      <div className="text-xs font-mono uppercase text-slate-400 mb-2 font-semibold">
                        Persisted Runs in Evidence Store ({evidenceList.length})
                      </div>
                      <div className="space-y-1.5 max-h-40 overflow-y-auto">
                        {evidenceList.map((run) => (
                          <div
                            key={run.run_id}
                            onClick={() => setActiveRunResult(run)}
                            className="flex items-center justify-between rounded p-2 text-xs font-mono bg-slate-950 hover:bg-slate-800 cursor-pointer border border-slate-800/60"
                          >
                            <span className="truncate w-48 text-slate-300">{run.run_id}</span>
                            <span
                              className={`rounded px-1.5 py-0.5 text-[10px] font-bold ${
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
          )}

          {/* TAB 5: M1 ACCEPTANCE */}
          {activeTab === 'acceptance' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <ShieldCheck className="h-5 w-5 text-blue-400" />
                  <span>M1 Independent Acceptance Review</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Reviews persisted M1 evidence without re-executing task or verifier. Strictly enforces frozen criteria (no provider call, no model call, scope exactness, verified vertical status).
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono uppercase text-slate-400 font-semibold">
                      M1 Summary Evidence Payload (JSON)
                    </span>
                  </div>
                  <textarea
                    rows={16}
                    value={m1Payload}
                    onChange={(e) => setM1Payload(e.target.value)}
                    className="w-full rounded border border-slate-700 bg-slate-950 p-2 font-mono text-[11px] text-slate-200 focus:border-blue-500 focus:outline-none"
                  />
                  <button
                    onClick={handleReviewAcceptance}
                    disabled={acceptanceLoading}
                    className="w-full rounded bg-blue-600 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-blue-500 disabled:opacity-50 transition"
                  >
                    {acceptanceLoading ? 'Reviewing...' : 'Perform Independent Acceptance Review'}
                  </button>
                </div>

                <div className="space-y-4">
                  {acceptanceResult ? (
                    <div className="space-y-4">
                      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-mono uppercase text-slate-400">Acceptance Decision</span>
                          <span
                            className={`rounded px-2.5 py-0.5 font-mono text-xs font-bold border ${
                              acceptanceResult.decision === 'ACCEPTED'
                                ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                                : 'bg-rose-950 text-rose-400 border-rose-800'
                            }`}
                          >
                            {acceptanceResult.status}
                          </span>
                        </div>
                        <div className="text-xs font-mono text-slate-300">
                          {acceptanceResult.reason}
                        </div>
                        {acceptanceResult.failures.length > 0 && (
                          <div className="mt-2 rounded bg-rose-950/40 p-2 border border-rose-800 font-mono text-xs text-rose-300">
                            <strong>Failures ({acceptanceResult.failures.length}):</strong>
                            <ul className="list-disc list-inside mt-1 space-y-0.5">
                              {acceptanceResult.failures.map((f, i) => (
                                <li key={i}>{f}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>

                      <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                        <div className="text-xs font-mono uppercase text-slate-400 mb-2 font-semibold">
                          Persisted Acceptance Record
                        </div>
                        <pre className="rounded bg-slate-950 p-3 font-mono text-[11px] text-slate-300 overflow-x-auto border border-slate-800">
                          {JSON.stringify(acceptanceResult.acceptance_record, null, 2)}
                        </pre>
                      </div>
                    </div>
                  ) : (
                    <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-8 text-center text-xs font-mono text-slate-500">
                      Click Perform Independent Acceptance Review to validate the JSON evidence record against frozen rules.
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 6: DECISION BASIS */}
          {activeTab === 'decision-basis' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <FileCheck className="h-5 w-5 text-blue-400" />
                  <span>AGENTS.md Decision Basis Generator</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  CodePro requires non-trivial engineering decisions to maintain an explicit, reviewable basis conforming to repository policy.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3 rounded-xl border border-slate-800 bg-slate-900/60 p-4">
                  <div>
                    <label className="text-[11px] font-mono text-slate-400">problem_class</label>
                    <input
                      type="text"
                      value={basisProblemClass}
                      onChange={(e) => setBasisProblemClass(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">decision (mechanism chosen)</label>
                    <input
                      type="text"
                      value={basisDecision}
                      onChange={(e) => setBasisDecision(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">basis_type</label>
                    <select
                      value={basisType}
                      onChange={(e) => setBasisType(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    >
                      <option value="STANDARD">STANDARD</option>
                      <option value="OFFICIAL_DOC">OFFICIAL_DOC</option>
                      <option value="UPSTREAM_IMPL">UPSTREAM_IMPL</option>
                      <option value="BENCHMARK">BENCHMARK</option>
                      <option value="PROJECT_INVARIANT">PROJECT_INVARIANT</option>
                      <option value="LOCAL_EVIDENCE">LOCAL_EVIDENCE</option>
                      <option value="LOCAL_DESIGN_HYPOTHESIS">LOCAL_DESIGN_HYPOTHESIS</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">basis_ref</label>
                    <input
                      type="text"
                      value={basisRef}
                      onChange={(e) => setBasisRef(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">supported_claim</label>
                    <input
                      type="text"
                      value={basisClaim}
                      onChange={(e) => setBasisClaim(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">applicability</label>
                    <input
                      type="text"
                      value={basisApplicability}
                      onChange={(e) => setBasisApplicability(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    />
                  </div>

                  <div>
                    <label className="text-[11px] font-mono text-slate-400">deviation</label>
                    <input
                      type="text"
                      value={basisDeviation}
                      onChange={(e) => setBasisDeviation(e.target.value)}
                      className="w-full rounded border border-slate-700 bg-slate-950 px-2 py-1.5 font-mono text-xs text-slate-200"
                    />
                  </div>

                  <button
                    onClick={handleGenerateDecisionBasis}
                    className="w-full rounded bg-blue-600 py-2 text-xs font-bold uppercase tracking-wider text-white hover:bg-blue-500 transition"
                  >
                    Format Decision Basis Block
                  </button>
                </div>

                <div className="space-y-4">
                  <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono uppercase text-slate-400 font-semibold">
                        Formatted Record (Ready for PR / ADR / Commit)
                      </span>
                      {basisOutput && (
                        <button
                          onClick={() => copyToClipboard(basisOutput)}
                          className="flex items-center space-x-1 rounded bg-slate-800 px-2 py-1 text-xs text-slate-200 hover:bg-slate-700 transition"
                        >
                          {copiedBasis ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                          <span>{copiedBasis ? 'Copied' : 'Copy'}</span>
                        </button>
                      )}
                    </div>
                    <pre className="rounded bg-slate-950 p-4 font-mono text-xs text-emerald-400 border border-slate-800 overflow-x-auto min-h-48">
                      {basisOutput || `problem_class = ${basisProblemClass}\ndecision = ${basisDecision}\nbasis_type = ${basisType}\nbasis_ref = ${basisRef}\nsupported_claim = ${basisClaim}\napplicability = ${basisApplicability}\ndeviation = ${basisDeviation}`}
                    </pre>
                  </div>

                  <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 text-xs text-slate-400 space-y-2">
                    <div className="font-semibold text-slate-300">Policy Rules from AGENTS.md:</div>
                    <div>• REFERENCE_FIT &gt; REFERENCE_COUNT</div>
                    <div>• Do not cite a source for a claim it does not support.</div>
                    <div>• Repeated workaround is a stop condition (REPEATED_WORKAROUND -&gt; ROOT_CAUSE_REFRAME -&gt; AUTHORITATIVE_RESEARCH).</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 7: FIXTURES */}
          {activeTab === 'fixtures' && (
            <div className="space-y-6 max-w-5xl">
              <div>
                <h2 className="text-xl font-bold text-white flex items-center space-x-2">
                  <Database className="h-5 w-5 text-blue-400" />
                  <span>Experiment & Contract Fixtures Explorer</span>
                </h2>
                <p className="text-sm text-slate-400 mt-1">
                  Explore the frozen fixtures, contracts, workload manifests, and study specifications from CodePro experiments.
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <span className="text-xs font-mono text-slate-400">Select Fixture:</span>
                <select
                  value={selectedFixtureKey}
                  onChange={(e) => setSelectedFixtureKey(e.target.value)}
                  className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 font-mono text-xs text-slate-100 focus:border-blue-500 focus:outline-none"
                >
                  {Object.keys(fixtures).map((key) => (
                    <option key={key} value={key}>
                      {fixtures[key].name} ({fixtures[key].type})
                    </option>
                  ))}
                </select>
              </div>

              {selectedFixtureKey && fixtures[selectedFixtureKey] && (
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-sm font-bold text-white">{fixtures[selectedFixtureKey].name}</h3>
                      <p className="text-xs text-slate-400">{fixtures[selectedFixtureKey].description}</p>
                    </div>
                    <span className="rounded bg-blue-950 px-2 py-0.5 font-mono text-xs text-blue-300 border border-blue-800">
                      {fixtures[selectedFixtureKey].type}
                    </span>
                  </div>

                  <pre className="rounded-lg bg-slate-950 p-4 font-mono text-[11px] text-slate-300 border border-slate-800 max-h-96 overflow-y-auto">
                    {JSON.stringify(fixtures[selectedFixtureKey].data, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
