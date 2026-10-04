import React, { useState, useEffect } from 'react';
import { Sliders, RefreshCw, Layers, Compass, Zap, HelpCircle } from 'lucide-react';

interface CharacterizationResponse {
  scope: string;
  recommended_path: string;
  confidence: string;
  reason_codes: string[];
  reasons: string[];
  characterized_at: string;
  authority: 'NON_AUTHORITATIVE_PREVIEW';
  preview_only: true;
  canonical_authority: string;
}

interface RoutingResponse {
  decision: string;
  action: string;
  selected_path: string;
  target_executor_tier: string;
  reasons: string[];
  authority: 'NON_AUTHORITATIVE_PREVIEW';
  preview_only: true;
  canonical_authority: string;
}

export function CharacterizeTab() {
  const [candidateFiles, setCandidateFiles] = useState(() => {
    return localStorage.getItem('codepro_char_files') || 'src/arkx/cli.py\ntests/test_cli.py';
  });
  const [affectedComponents, setAffectedComponents] = useState(() => {
    return localStorage.getItem('codepro_char_components') || 'cli, chassis';
  });
  const [ambiguityMarkers, setAmbiguityMarkers] = useState(() => {
    return localStorage.getItem('codepro_char_ambiguity') || '';
  });
  const [riskMarkers, setRiskMarkers] = useState(() => {
    return localStorage.getItem('codepro_char_risk') || '';
  });
  const [archChange, setArchChange] = useState(() => {
    return localStorage.getItem('codepro_char_arch') === 'true';
  });
  const [sharedState, setSharedState] = useState(() => {
    return localStorage.getItem('codepro_char_shared') === 'true';
  });

  const [charResult, setCharResult] = useState<CharacterizationResponse | null>(() => {
    const saved = localStorage.getItem('codepro_char_result');
    return saved ? JSON.parse(saved) : null;
  });
  const [routingResult, setRoutingResult] = useState<RoutingResponse | null>(() => {
    const saved = localStorage.getItem('codepro_routing_result');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  // Auto-sync states to localStorage
  useEffect(() => {
    localStorage.setItem('codepro_char_files', candidateFiles);
    localStorage.setItem('codepro_char_components', affectedComponents);
    localStorage.setItem('codepro_char_ambiguity', ambiguityMarkers);
    localStorage.setItem('codepro_char_risk', riskMarkers);
    localStorage.setItem('codepro_char_arch', String(archChange));
    localStorage.setItem('codepro_char_shared', String(sharedState));
  }, [candidateFiles, affectedComponents, ambiguityMarkers, riskMarkers, archChange, sharedState]);

  const loadPreset = (preset: 'simple' | 'localized' | 'repo' | 'ambiguous') => {
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

  const handleEvaluate = async () => {
    setLoading(true);
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

      // Characterize API
      const charRes = await fetch('/api/characterize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ signals }),
      });
      const charJson = await charRes.json();
      setCharResult(charJson);
      localStorage.setItem('codepro_char_result', JSON.stringify(charJson));

      // Route API
      const routeRes = await fetch('/api/routing', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          characterization: charJson,
          escalation_budget: 2,
          current_escalation_level: 0,
        }),
      });
      const routeJson = await routeRes.json();
      setRoutingResult(routeJson);
      localStorage.setItem('codepro_routing_result', JSON.stringify(routeJson));
    } catch (err) {
      console.error('Failed to characterize task', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <Sliders className="h-5 w-5 text-indigo-400" />
          <span>Task Characterization & Routing (P1 - P3 Preview)</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Simulate deterministic classification and routing based on code-change metadata to identify appropriate execution tiers.
        </p>
      </div>

      {/* Synthetic Fixture Preset Selectors */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-3 py-1 bg-slate-900/40 p-4 rounded-xl border border-slate-800">
        <span className="text-xs font-mono text-slate-400 font-medium">Load Workspace Presets:</span>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => loadPreset('simple')}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-mono text-slate-300 hover:bg-slate-700 transition border border-slate-700 cursor-pointer"
          >
            Simple (Single-File)
          </button>
          <button
            onClick={() => loadPreset('localized')}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-mono text-slate-300 hover:bg-slate-700 transition border border-slate-700 cursor-pointer"
          >
            Localized (Bounded)
          </button>
          <button
            onClick={() => loadPreset('repo')}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-mono text-slate-300 hover:bg-slate-700 transition border border-slate-700 cursor-pointer"
          >
            Repository-Wide
          </button>
          <button
            onClick={() => loadPreset('ambiguous')}
            className="rounded-lg bg-slate-800 px-3 py-1.5 text-xs font-mono text-slate-300 hover:bg-slate-700 transition border border-slate-700 cursor-pointer"
          >
            Ambiguous Issue
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Form Inputs */}
        <div className="lg:col-span-6 space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold mb-1">
            Explicit Signal Inputs
          </h3>

          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Candidate Files (one relative path per line)
              </label>
              <textarea
                rows={3}
                value={candidateFiles}
                onChange={(e) => setCandidateFiles(e.target.value)}
                placeholder="e.g. src/arkx/cli.py"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Affected Components (comma-separated list)
              </label>
              <input
                type="text"
                value={affectedComponents}
                onChange={(e) => setAffectedComponents(e.target.value)}
                placeholder="e.g. cli, core, chassis"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1">
                Ambiguity Markers (triggers fail-closed validation)
              </label>
              <input
                type="text"
                value={ambiguityMarkers}
                onChange={(e) => setAmbiguityMarkers(e.target.value)}
                placeholder="e.g. vague spec, missing files"
                className="w-full rounded-lg border border-slate-800 bg-slate-950 px-3 py-2 font-mono text-xs text-slate-200 focus:border-indigo-500 focus:outline-none"
              />
            </div>

            <div className="flex items-center gap-5 py-1">
              <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={archChange}
                  onChange={(e) => setArchChange(e.target.checked)}
                  className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-0 focus:ring-offset-0"
                />
                <span>Architectural Change</span>
              </label>
              <label className="flex items-center space-x-2 text-xs text-slate-300 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={sharedState}
                  onChange={(e) => setSharedState(e.target.checked)}
                  className="rounded border-slate-800 bg-slate-950 text-indigo-600 focus:ring-0 focus:ring-offset-0"
                />
                <span>Shared State Mutated</span>
              </label>
            </div>

            <button
              onClick={handleEvaluate}
              disabled={loading}
              className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 py-3 text-xs font-bold uppercase tracking-wider text-white transition disabled:opacity-50 flex items-center justify-center space-x-2 cursor-pointer"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin" />
                  <span>Evaluating signals...</span>
                </>
              ) : (
                <>
                  <Sliders className="h-4 w-4" />
                  <span>Run Characterization & Routing</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column: Output Previews */}
        <div className="lg:col-span-6 space-y-4">
          {charResult ? (
            <div className="space-y-4">
              {/* Classification Card */}
              <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono uppercase text-slate-400 font-bold flex items-center space-x-1">
                    <Layers className="h-3.5 w-3.5 text-indigo-400" />
                    <span>P1 Scope Characterization</span>
                  </span>
                  <span className="text-xs font-mono font-bold text-indigo-300">
                    {charResult.scope}
                  </span>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                    <span className="text-slate-400 font-mono">Recommended Path</span>
                    <strong className="text-white">{charResult.recommended_path}</strong>
                  </div>
                  <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                    <span className="text-slate-400 font-mono">Confidence Assessment</span>
                    <strong className="text-emerald-400">{charResult.confidence}</strong>
                  </div>
                </div>

                <div className="text-xs space-y-1">
                  <span className="text-slate-400 font-semibold block">Decision Basis Rationale:</span>
                  <ul className="list-disc list-inside text-slate-300 space-y-1 pl-1">
                    {charResult.reasons.map((r, i) => (
                      <li key={i} className="leading-relaxed">{r}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Routing Card */}
              {routingResult && (
                <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-mono uppercase text-slate-400 font-bold flex items-center space-x-1">
                      <Compass className="h-3.5 w-3.5 text-emerald-400" />
                      <span>P3 Routing Decisions</span>
                    </span>
                    <span className="text-xs font-mono font-bold text-emerald-300">
                      {routingResult.decision}
                    </span>
                  </div>

                  <div className="space-y-2 text-xs">
                    <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                      <span className="text-slate-400 font-mono">Escalation Threshold</span>
                      <strong className="text-white">{routingResult.action}</strong>
                    </div>
                    <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                      <span className="text-slate-400 font-mono">Target Hardware Tier</span>
                      <strong className="text-indigo-400">{routingResult.target_executor_tier}</strong>
                    </div>
                  </div>

                  <div className="text-xs space-y-1">
                    <span className="text-slate-400 font-semibold block">Enforced Policy Rules:</span>
                    <ul className="list-disc list-inside text-slate-300 space-y-1 pl-1">
                      {routingResult.reasons.map((r, i) => (
                        <li key={i} className="leading-relaxed">{r}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500 flex flex-col items-center justify-center h-full min-h-[300px]">
              <HelpCircle className="h-10 w-10 text-slate-600 mb-3" />
              <p className="text-sm font-medium text-slate-400">Awaiting Signal Inputs</p>
              <p className="text-xs text-slate-500 mt-1 max-w-xs leading-relaxed">
                Load a preset or input changes on the left and trigger evaluation to view classifications.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
