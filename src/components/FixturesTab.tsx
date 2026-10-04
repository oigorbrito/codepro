import React, { useState, useEffect } from 'react';
import { Database, HelpCircle } from 'lucide-react';

interface FixtureSummary {
  name: string;
  type: string;
  description: string;
  data: unknown;
}

export function FixturesTab() {
  const [fixtures, setFixtures] = useState<Record<string, FixtureSummary>>({});
  const [selectedKey, setSelectedFixtureKey] = useState(() => {
    return localStorage.getItem('codepro_fixtures_selected') || '';
  });

  const fetchFixtures = async () => {
    try {
      const res = await fetch('/api/fixtures');
      if (res.ok) {
        const data = await res.json();
        setFixtures(data);
        
        // Auto-select first key if none loaded/saved
        const keys = Object.keys(data);
        if (keys.length > 0 && !selectedKey) {
          setSelectedFixtureKey(keys[0]);
          localStorage.setItem('codepro_fixtures_selected', keys[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch experiment fixtures', err);
    }
  };

  useEffect(() => {
    fetchFixtures();
  }, []);

  const handleSelectKey = (key: string) => {
    setSelectedFixtureKey(key);
    localStorage.setItem('codepro_fixtures_selected', key);
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h2 className="text-xl font-bold text-slate-100 flex items-center space-x-2">
          <Database className="h-5 w-5 text-indigo-400" />
          <span>Experiment & Contract Fixtures Explorer</span>
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Explore frozen contract fixtures, workload manifests, and study specifications from CodePro's core database.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center gap-3">
        <span className="text-xs font-mono text-slate-400 font-semibold shrink-0">Select Active Fixture:</span>
        <select
          value={selectedKey}
          onChange={(e) => handleSelectKey(e.target.value)}
          className="flex-1 rounded-lg border border-slate-800 bg-slate-900 px-3 py-2.5 font-mono text-xs text-slate-100 focus:outline-none focus:border-indigo-500 cursor-pointer"
        >
          {Object.keys(fixtures).length === 0 ? (
            <option value="">No fixtures loaded</option>
          ) : (
            Object.keys(fixtures).map((key) => (
              <option key={key} value={key}>
                {fixtures[key].name} ({fixtures[key].type})
              </option>
            ))
          )}
        </select>
      </div>

      {selectedKey && fixtures[selectedKey] ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800/60 gap-2">
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">{fixtures[selectedKey].name}</h3>
              <p className="text-xs text-slate-400 mt-0.5">{fixtures[selectedKey].description}</p>
            </div>
            <span className="rounded-lg bg-indigo-950 border border-indigo-900/60 px-3 py-1 font-mono text-xs font-semibold text-indigo-300 self-start sm:self-auto">
              {fixtures[selectedKey].type}
            </span>
          </div>

          <pre className="rounded-xl bg-slate-950 p-4 font-mono text-[11px] text-slate-300 border border-slate-800 max-h-[440px] overflow-y-auto leading-relaxed">
            {JSON.stringify(fixtures[selectedKey].data, null, 2)}
          </pre>
        </div>
      ) : (
        <div className="rounded-xl border border-dashed border-slate-800 bg-slate-900/20 p-12 text-center text-slate-500 flex flex-col items-center justify-center min-h-[220px]">
          <HelpCircle className="h-10 w-10 text-slate-600 mb-3" />
          <p className="text-sm font-medium text-slate-400">No Fixture Active</p>
          <p className="text-xs text-slate-500 mt-1">
            Unable to locate fixtures under the /experiments directory. Make sure JSON manifests exist.
          </p>
        </div>
      )}
    </div>
  );
}
