import React, { useState, useEffect } from 'react';
import { Search, Folder, RefreshCw, CheckCircle2, AlertTriangle, Layers, ShieldCheck } from 'lucide-react';

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

export function InspectTab() {
  const [pathInput, setPathInput] = useState(() => {
    return localStorage.getItem('codepro_inspect_path') || '.';
  });
  const [data, setData] = useState<InspectionResponse | null>(() => {
    const saved = localStorage.getItem('codepro_inspect_data');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  const handleInspect = async () => {
    setLoading(true);
    localStorage.setItem('codepro_inspect_path', pathInput);
    try {
      const res = await fetch('/api/inspect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: pathInput }),
      });
      if (res.ok) {
        const json = await res.json();
        setData(json);
        localStorage.setItem('codepro_inspect_data', JSON.stringify(json));
      }
    } catch (err) {
      console.error('Failed to run project inspect', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!data) {
      handleInspect();
    }
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <Search className="h-5 w-5 text-indigo-400" />
          <span>Project Inspection (codepro inspect)</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Perform a read-only query of local project context, including Git properties, languages, testing surfaces, and available executors.
        </p>
      </div>

      <div className="flex items-center gap-3">
        <div className="relative flex-1">
          <Folder className="absolute left-3.5 top-3 h-4 w-4 text-slate-500" />
          <input
            type="text"
            value={pathInput}
            onChange={(e) => setPathInput(e.target.value)}
            placeholder="Target workspace directory (e.g. .)"
            className="w-full rounded-lg border border-slate-800 bg-slate-900 pl-11 pr-4 py-2.5 font-mono text-sm text-slate-100 placeholder-slate-500 focus:border-indigo-500 focus:outline-none"
          />
        </div>
        <button
          onClick={handleInspect}
          disabled={loading}
          className="rounded-lg bg-indigo-600 hover:bg-indigo-500 px-5 py-2.5 text-sm font-semibold text-white transition disabled:opacity-50 flex items-center space-x-2 shrink-0 cursor-pointer"
        >
          {loading ? (
            <>
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Inspecting...</span>
            </>
          ) : (
            <>
              <Search className="h-4 w-4" />
              <span>Inspect Workspace</span>
            </>
          )}
        </button>
      </div>

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Left Card: Git & Workspace */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5">
                <Layers className="h-3.5 w-3.5 text-indigo-400" />
                <span>Workspace Context</span>
              </h3>
              
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Project Name</span>
                  <strong className="text-white font-medium">{data.project_name}</strong>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Project Root</span>
                  <span className="text-slate-300 font-mono text-xs max-w-[280px] truncate" title={data.project_root}>
                    {data.project_root}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Git CLI Available</span>
                  <span className={`font-mono text-xs font-semibold ${data.git_available ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {data.git_available ? 'YES' : 'NO'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1 border-b border-slate-800/40">
                  <span className="text-slate-400">Git Repository Initialized</span>
                  <span className={`font-mono text-xs font-semibold ${data.git_repository ? 'text-emerald-400' : 'text-amber-400'}`}>
                    {data.git_repository ? 'YES' : 'NO'}
                  </span>
                </div>
                <div className="flex items-center justify-between py-1">
                  <span className="text-slate-400">Active Branch</span>
                  <span className="text-indigo-400 font-mono text-xs font-bold">
                    {data.branch || 'N/A'}
                  </span>
                </div>
              </div>
            </div>

            {/* Right Card: Languages & Testing Surfaces */}
            <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
              <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold flex items-center space-x-1.5">
                <ShieldCheck className="h-3.5 w-3.5 text-indigo-400" />
                <span>Languages & Testing Surfaces</span>
              </h3>

              <div className="space-y-4">
                <div>
                  <div className="text-xs font-mono text-slate-500 mb-2">DETECTED LANGUAGES</div>
                  <div className="flex flex-wrap gap-2">
                    {data.languages.length > 0 ? (
                      data.languages.map((lang) => (
                        <span
                          key={lang}
                          className="rounded-lg bg-slate-800 border border-slate-700/60 px-3 py-1 text-xs font-medium text-slate-300"
                        >
                          {lang}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 font-mono italic">No language directories detected</span>
                    )}
                  </div>
                </div>

                <div>
                  <div className="text-xs font-mono text-slate-500 mb-2">TEST SURFACES</div>
                  <div className="flex flex-wrap gap-2">
                    {data.test_surfaces.length > 0 ? (
                      data.test_surfaces.map((surface) => (
                        <span
                          key={surface}
                          className="rounded-lg bg-indigo-950/40 border border-indigo-900/60 px-3 py-1 text-xs font-medium text-indigo-300"
                        >
                          {surface}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500 font-mono italic">No test paths detected</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Bottom Card: Executors */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 font-semibold">
              Available Coding Executor Binaries in Host PATH
            </h3>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
              {data.executors.map((exec) => (
                <div
                  key={exec.name}
                  className="rounded-xl border border-slate-800/80 bg-slate-950 p-4 flex items-center justify-between"
                >
                  <div className="space-y-0.5">
                    <div className="text-sm font-bold text-slate-200">{exec.name}</div>
                    <div className="text-xs font-mono text-slate-500 truncate max-w-[180px]" title={exec.command}>
                      {exec.command}
                    </div>
                  </div>
                  <span
                    className={`rounded-lg px-2.5 py-1 text-[10px] font-mono font-bold tracking-wider ${
                      exec.available
                        ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                        : 'bg-slate-800 text-slate-400'
                    }`}
                  >
                    {exec.available ? 'PRESENT' : 'ABSENT'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
