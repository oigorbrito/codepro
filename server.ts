import express from 'express';
import { createServer as createViteServer } from 'vite';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';
import { execFileSync } from 'child_process';

import { CHASSIS_FINGERPRINT, CHASSIS_VERSION, SCHEMA_VERSION } from './src/chassis/contracts';
import { inspectProject } from './src/chassis/inspection';
import { characterizeTask } from './src/chassis/characterization';
import { assessProgress } from './src/chassis/progress';
import { evaluateRouting } from './src/chassis/routing';
import { executeVertical, getRunEvidence, listRunEvidence } from './src/chassis/vertical';
import { reviewM1Evidence } from './src/chassis/m1Acceptance';
import { loadFixtures } from './src/chassis/fixtures';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = Number(process.env.PORT) || 3000;
const HOST = '0.0.0.0';

app.use(express.json());

// API Routes

// 1. Doctor / Runtime health check
app.get('/api/doctor', (req, res) => {
  let gitVersion: string | null = null;
  let pythonVersion: string | null = null;

  const pythonExecutable = process.env.CODEPRO_PYTHON?.trim() || null;

  try {
    gitVersion = execFileSync(
      'git',
      ['--version'],
      { encoding: 'utf8' },
    ).trim();
  } catch {
    gitVersion = null;
  }

  if (pythonExecutable) {
    try {
      pythonVersion = execFileSync(
        pythonExecutable,
        ['--version'],
        { encoding: 'utf8' },
      ).trim();
    } catch {
      pythonVersion = null;
    }
  }

  const checks = [
    {
      name: 'node_runtime',
      label: 'Node.js Runtime',
      ok: true,
      detail: process.version,
      required: '>=20.0.0',
    },
    {
      name: 'chassis_schema',
      label: 'Telemetry Schema Contract',
      ok: true,
      detail: `v${SCHEMA_VERSION} fail-closed`,
    },
    {
      name: 'chassis_version',
      label: 'Chassis Package Version',
      ok: true,
      detail: CHASSIS_VERSION,
    },
    {
      name: 'chassis_fingerprint',
      label: 'Chassis Fingerprint',
      ok: true,
      detail: CHASSIS_FINGERPRINT,
    },
    {
      name: 'git_binary',
      label: 'Git CLI Integration',
      ok: !!gitVersion,
      detail: gitVersion || 'not installed',
    },
    {
      name: 'python_runtime',
      label: 'Python Execution Core (CODEPRO_PYTHON)',
      ok: !!pythonExecutable && !!pythonVersion,
      detail: !pythonExecutable
        ? 'CODEPRO_PYTHON not configured'
        : pythonVersion || `failed to execute ${pythonExecutable}`,
      required: 'explicit CODEPRO_PYTHON binding',
    },
  ];

  const overall = checks.every((check) => check.ok);

  res.json({
    status: overall ? 'PASS' : 'FAIL',
    timestamp: new Date().toISOString(),
    checks,
  });
});

// 2. Project Inspection (codepro inspect)
app.post('/api/inspect', (req, res) => {
  try {
    const targetPath = req.body?.path || '.';
    const inspection = inspectProject(targetPath);
    res.json(inspection);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown inspection error';
    res.status(400).json({ error: message });
  }
});

// 3. Task Characterization (P1)
app.post('/api/characterize', (req, res) => {
  try {
    const signals = req.body?.signals || {};
    const result = characterizeTask(signals);
    res.json({
      ...result,
      authority: 'NON_AUTHORITATIVE_PREVIEW',
      preview_only: true,
      canonical_authority: 'src/arkx/characterization.py',
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    res.status(400).json({ error: message });
  }
});

// 4. Progress Assessment (P2)
app.post('/api/assess-progress', (req, res) => {
  try {
    const result = assessProgress(req.body);
    res.json({
      ...result,
      authority: 'NON_AUTHORITATIVE_PREVIEW',
      preview_only: true,
      canonical_authority: 'src/arkx/progress.py',
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    res.status(400).json({ error: message });
  }
});

// 5. Routing Evaluation (P3)
app.post('/api/routing', (req, res) => {
  try {
    const result = evaluateRouting(req.body);
    res.json({
      ...result,
      authority: 'NON_AUTHORITATIVE_PREVIEW',
      preview_only: true,
      canonical_authority: 'src/arkx/routing.py',
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    res.status(400).json({ error: message });
  }
});

// 6. Vertical Journey Execution (codepro run)
app.post('/api/vertical/run', (req, res) => {
  try {
    const input = req.body;
    if (!input.request_id || !input.task_id || !input.scope) {
      return res.status(400).json({ error: 'Missing required run parameters (request_id, task_id, scope)' });
    }
    const result = executeVertical(input);
    res.json(result);
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown execution error';
    res.status(500).json({ error: message });
  }
});

// 7. List and Query Run Evidence
app.get('/api/evidence', (req, res) => {
  res.json(listRunEvidence());
});

app.get('/api/evidence/:id', (req, res) => {
  const item = getRunEvidence(req.params.id);
  if (!item) {
    return res.status(404).json({ error: 'Evidence record not found' });
  }
  res.json(item);
});

// 8. M1 Acceptance Review (codepro accept)
app.post('/api/m1/review', (req, res) => {
  try {
    const preview = reviewM1Evidence(req.body);
    const previewDecision =
      preview.decision === 'ACCEPTED'
        ? 'WOULD_ACCEPT'
        : 'WOULD_REJECT';

    res.json({
      decision: previewDecision,
      status: 'NON_AUTHORITATIVE_PREVIEW',
      authority: 'NON_AUTHORITATIVE_PREVIEW',
      preview_only: true,
      reason: preview.reason,
      failures: preview.failures,
      reviewed_at: preview.reviewed_at,
      acceptance_record: {
        authoritative: false,
        preview_only: true,
        preview_decision: previewDecision,
        canonical_authority: 'src/arkx/acceptance.py',
        failures: preview.failures,
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Review error';
    res.status(400).json({ error: message });
  }
});

// 9. Experiment Fixtures
app.get('/api/fixtures', (req, res) => {
  res.json(loadFixtures());
});

// 10. AGENTS.md Decision Basis helper
app.post('/api/decision-basis', (req, res) => {
  const {
    problem_class,
    decision,
    basis_type,
    basis_ref,
    supported_claim,
    applicability,
    deviation,
  } = req.body;

  const validTypes = [
    'STANDARD',
    'OFFICIAL_DOC',
    'UPSTREAM_IMPL',
    'BENCHMARK',
    'PROJECT_INVARIANT',
    'LOCAL_EVIDENCE',
    'LOCAL_DESIGN_HYPOTHESIS',
  ];

  if (!problem_class || !decision || !basis_type || !basis_ref) {
    return res.status(400).json({ error: 'Missing required Decision Basis fields' });
  }

  if (!validTypes.includes(basis_type)) {
    return res.status(400).json({ error: `basis_type must be one of: ${validTypes.join(', ')}` });
  }

  const formatted = `problem_class = ${problem_class}
decision = ${decision}
basis_type = ${basis_type}
basis_ref = ${basis_ref}
supported_claim = ${supported_claim || 'N/A'}
applicability = ${applicability || 'N/A'}
deviation = ${deviation || 'none'}`;

  res.json({
    valid: true,
    formatted,
    record: {
      problem_class,
      decision,
      basis_type,
      basis_ref,
      supported_claim,
      applicability,
      deviation,
    },
  });
});

// Setup Vite middleware or static serving
async function setupServer() {
  if (process.env.NODE_ENV === 'production' && fs.existsSync(path.resolve(__dirname, 'dist'))) {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  } else {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  }

  app.listen(PORT, HOST, () => {
    console.log(`CodePro server running on http://${HOST}:${PORT}`);
  });
}

setupServer().catch((err) => {
  console.error('Failed to start server:', err);
  process.exit(1);
});
