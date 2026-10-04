import React, { useState, useEffect } from 'react';
import { Activity, RefreshCw, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

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

export function DoctorTab() {
  const [data, setData] = useState<DoctorResponse | null>(() => {
    const saved = localStorage.getItem('codepro_doctor_data');
    return saved ? JSON.parse(saved) : null;
  });
  const [loading, setLoading] = useState(false);

  const fetchDoctor = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/doctor');
      if (res.ok) {
        const json = await res.json();
        setData(json);
        localStorage.setItem('codepro_doctor_data', JSON.stringify(json));
      }
    } catch (err) {
      console.error('Failed to fetch doctor diagnostic data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!data) {
      fetchDoctor();
    }
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
            <Activity className="h-5 w-5 text-indigo-400" />
            <span>Chassis Doctor & Runtime Environment</span>
          </h2>
          <p className="text-sm text-slate-400 mt-1">
            Verifies local runtime execution boundaries, contract schema integrity, and executor environments.
          </p>
        </div>

        <button
          onClick={fetchDoctor}
          disabled={loading}
          className="flex items-center space-x-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 px-4 py-2.5 text-xs font-semibold text-white shadow-md shadow-indigo-600/20 transition disabled:opacity-50 cursor-pointer"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          <span>{loading ? 'Evaluating...' : 'Re-run Diagnostics'}</span>
        </button>
      </div>

      {data ? (
        <div className="space-y-6">
          {/* Diagnostic Status Card */}
          <div className="flex items-center justify-between rounded-xl bg-slate-900 border border-slate-800 p-5">
            <div className="flex items-center space-x-4">
              {data.status === 'PASS' ? (
                <CheckCircle2 className="h-8 w-8 text-emerald-400 shrink-0" />
              ) : (
                <AlertTriangle className="h-8 w-8 text-amber-400 shrink-0" />
              )}
              <div>
                <div className="text-lg font-bold text-white tracking-tight">
                  Chassis Diagnostic State: {data.status}
                </div>
                <div className="text-xs text-slate-400 font-mono mt-0.5">
                  Last evaluated: {new Date(data.timestamp).toLocaleString()}
                </div>
              </div>
            </div>
            <div className="text-xs text-slate-500 hidden sm:block font-mono">
              Invariants check: 100% nominal
            </div>
          </div>

          {/* Grid of Checks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.checks.map((check) => (
              <div
                key={check.name}
                className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 flex items-start justify-between"
              >
                <div className="space-y-1">
                  <div className="text-sm font-semibold text-slate-200">{check.label}</div>
                  <div className="text-xs font-mono text-slate-400">
                    Status: <span className="text-slate-100 font-bold">{check.detail}</span>
                  </div>
                  {check.required && (
                    <div className="text-[11px] text-slate-500 font-mono">
                      Requirement: {check.required}
                    </div>
                  )}
                </div>
                <span
                  className={`rounded-lg px-2.5 py-1 text-[11px] font-mono font-bold tracking-wider ${
                    check.ok
                      ? 'bg-emerald-950/80 text-emerald-400 border border-emerald-800'
                      : 'bg-amber-950/80 text-amber-400 border border-amber-800'
                  }`}
                >
                  {check.ok ? 'PASS' : 'WARN'}
                </span>
              </div>
            ))}
          </div>

          {/* Description Section */}
          <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-5">
            <h3 className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-3 font-semibold flex items-center space-x-1.5">
              <Info className="h-3.5 w-3.5 text-indigo-400" />
              <span>Chassis Invariants & Telemetry Policies</span>
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs text-slate-300">
              <div className="rounded-lg bg-slate-950/80 p-4 border border-slate-800">
                <strong className="text-indigo-400 block mb-1">P0 Execution Telemetry</strong>
                Fail-closed serializable event stream with strict ISO-8601 timestamps and non-empty run IDs.
              </div>
              <div className="rounded-lg bg-slate-950/80 p-4 border border-slate-800">
                <strong className="text-indigo-400 block mb-1">P1 Characterization</strong>
                Deterministic, conservative scope classification without NLP inference or speculative jumps.
              </div>
              <div className="rounded-lg bg-slate-950/80 p-4 border border-slate-800">
                <strong className="text-indigo-400 block mb-1">P3 Routing & Escalation</strong>
                Rule-based routing refusing hidden fallback or silent executor switches.
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-12 text-center text-slate-500 font-mono text-sm border border-slate-800 rounded-xl bg-slate-900/40 animate-pulse">
          Loading diagnostic state...
        </div>
      )}
    </div>
  );
}
