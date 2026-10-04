import React, { useState, useEffect } from 'react';
import { FileCheck, Copy, Check, Info } from 'lucide-react';

export function DecisionBasisTab() {
  const [problemClass, setProblemClass] = useState(() => localStorage.getItem('codepro_db_problem') || 'runtime_chassis_migration');
  const [decision, setDecision] = useState(() => localStorage.getItem('codepro_db_decision') || 'migrate to Node.js 22 full-stack Express + Vite React SPA');
  const [basisType, setBasisType] = useState(() => localStorage.getItem('codepro_db_type') || 'OFFICIAL_DOC');
  const [basisRef, setBasisRef] = useState(() => localStorage.getItem('codepro_db_ref') || '/skills/system_skills/github_import_migration/references/web.md');
  const [supportedClaim, setSupportedClaim] = useState(() => localStorage.getItem('codepro_db_claim') || 'Python repositories converted to Node.js web services with port 3000 entry point');
  const [applicability, setApplicability] = useState(() => localStorage.getItem('codepro_db_applicability') || 'AI Studio web environment constraints require port 3000 Node.js dev server');
  const [deviation, setDeviation] = useState(() => localStorage.getItem('codepro_db_deviation') || 'none');

  const [formattedOutput, setFormattedOutput] = useState('');
  const [copied, setCopied] = useState(false);

  // Sync to local storage
  useEffect(() => {
    localStorage.setItem('codepro_db_problem', problemClass);
    localStorage.setItem('codepro_db_decision', decision);
    localStorage.setItem('codepro_db_type', basisType);
    localStorage.setItem('codepro_db_ref', basisRef);
    localStorage.setItem('codepro_db_claim', supportedClaim);
    localStorage.setItem('codepro_db_applicability', applicability);
    localStorage.setItem('codepro_db_deviation', deviation);
  }, [problemClass, decision, basisType, basisRef, supportedClaim, applicability, deviation]);

  const handleGenerate = async () => {
    try {
      const res = await fetch('/api/decision-basis', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          problem_class: problemClass,
          decision,
          basis_type: basisType,
          basis_ref: basisRef,
          supported_claim: supportedClaim,
          applicability,
          deviation,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.formatted) {
          setFormattedOutput(json.formatted);
        }
      }
    } catch (err) {
      console.error(err);
    }
  };

  const copyToClipboard = () => {
    const textToCopy = formattedOutput || `problem_class = ${problemClass}\ndecision = ${decision}\nbasis_type = ${basisType}\nbasis_ref = ${basisRef}\nsupported_claim = ${supportedClaim}\napplicability = ${applicability}\ndeviation = ${deviation}`;
    navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <FileCheck className="h-5 w-5 text-indigo-400" />
          <span>AGENTS.md Decision Basis Generator</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Generate structured, reviewable decision blocks conforming to CodePro's core policy rules for PRs, commits, and architectural documentation.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left Form: Parameters */}
        <div className="space-y-4 rounded-xl border border-slate-800 bg-slate-900/60 p-5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-bold mb-1">
            Decision Signals
          </h3>

          <div className="space-y-3.5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">problem_class</label>
              <input
                type="text"
                value={problemClass}
                onChange={(e) => setProblemClass(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">decision (mechanism chosen)</label>
              <input
                type="text"
                value={decision}
                onChange={(e) => setDecision(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">basis_type</label>
              <select
                value={basisType}
                onChange={(e) => setBasisType(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-indigo-500 cursor-pointer"
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
              <label className="block text-xs font-semibold text-slate-300 mb-1">basis_ref</label>
              <input
                type="text"
                value={basisRef}
                onChange={(e) => setBasisRef(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">supported_claim</label>
              <input
                type="text"
                value={supportedClaim}
                onChange={(e) => setSupportedClaim(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">applicability</label>
              <input
                type="text"
                value={applicability}
                onChange={(e) => setApplicability(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">deviation</label>
              <input
                type="text"
                value={deviation}
                onChange={(e) => setDeviation(e.target.value)}
                className="w-full rounded-lg bg-slate-950 border border-slate-800 px-3 py-1.5 font-mono text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>

            <button
              onClick={handleGenerate}
              className="w-full rounded-lg bg-indigo-600 hover:bg-indigo-500 py-2.5 text-xs font-bold uppercase tracking-wider text-white transition cursor-pointer"
            >
              Format Decision Basis Block
            </button>
          </div>
        </div>

        {/* Right Card: Output Block */}
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono uppercase text-slate-400 font-bold">
                Formatted Block Output
              </span>
              <button
                onClick={copyToClipboard}
                className="flex items-center space-x-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 px-3 py-1.5 text-xs text-slate-300 border border-slate-700 transition cursor-pointer"
              >
                {copied ? <Check className="h-3.5 w-3.5 text-emerald-400 animate-scale" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copied ? 'Copied!' : 'Copy'}</span>
              </button>
            </div>

            <pre className="rounded-lg bg-slate-950 p-4 font-mono text-xs text-emerald-400 border border-slate-800 overflow-x-auto min-h-[220px] leading-relaxed">
              {formattedOutput || `problem_class = ${problemClass}\ndecision = ${decision}\nbasis_type = ${basisType}\nbasis_ref = ${basisRef}\nsupported_claim = ${supportedClaim}\napplicability = ${applicability}\ndeviation = ${deviation}`}
            </pre>
          </div>

          {/* Core Policy rules */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-4 flex items-start space-x-3 text-xs text-slate-400 leading-normal">
            <Info className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
            <div className="space-y-1.5">
              <span className="font-semibold text-slate-300">Decision Discipline Rules:</span>
              <p>• <strong>REFERENCE_FIT &gt; REFERENCE_COUNT</strong>: Focus on exact matching and accuracy.</p>
              <p>• Do not cite a source for a claim it does not support.</p>
              <p>• <strong>REPEATED_WORKAROUND</strong>: Multi-workaround attempts is a stop condition (ROOT_CAUSE_REFRAME -&gt; AUTHORITATIVE_RESEARCH).</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
