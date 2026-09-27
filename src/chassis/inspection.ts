/**
 * Read-only project inspection for CodePro.
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const LANGUAGE_MARKERS: Array<[string, string[]]> = [
  ['TypeScript', ['tsconfig.json']],
  ['JavaScript', ['package.json']],
  ['Python', ['pyproject.toml', 'setup.py', 'setup.cfg', 'requirements.txt']],
  ['Go', ['go.mod']],
  ['Rust', ['Cargo.toml']],
  ['Java', ['pom.xml', 'build.gradle', 'build.gradle.kts']],
];

const KNOWN_EXECUTORS: Array<[string, string]> = [
  ['Codex CLI', 'codex'],
  ['Claude Code', 'claude'],
  ['Gemini CLI', 'gemini'],
  ['mini-SWE-agent', 'mini-swe-agent'],
  ['SWE-agent', 'swe-agent'],
  ['OpenHands', 'openhands'],
];

export interface ExecutorStatus {
  name: string;
  command: string;
  available: boolean;
}

export interface ProjectInspectionResult {
  project_name: string;
  project_root: string;
  git_available: boolean;
  git_repository: boolean;
  branch: string | null;
  languages: string[];
  test_surfaces: string[];
  executors: ExecutorStatus[];
  timestamp: string;
}

function checkCommand(cmd: string): boolean {
  try {
    execSync(`which ${cmd} 2>/dev/null`);
    return true;
  } catch {
    return false;
  }
}

function runGit(cwd: string, args: string): string | null {
  try {
    return execSync(`git -C "${cwd}" ${args} 2>/dev/null`, { timeout: 3000 })
      .toString()
      .trim() || null;
  } catch {
    return null;
  }
}

export function inspectProject(targetPath: string = '.'): ProjectInspectionResult {
  const resolved = path.resolve(targetPath);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
    throw new Error(`Project path is not a directory: ${resolved}`);
  }

  const gitAvailable = checkCommand('git');
  let gitRepo = false;
  let branch: string | null = null;
  let rootDir = resolved;

  if (gitAvailable) {
    const toplevel = runGit(resolved, 'rev-parse --show-toplevel');
    if (toplevel) {
      gitRepo = true;
      rootDir = path.resolve(toplevel);
      branch = runGit(rootDir, 'branch --show-current');
      if (!branch) {
        const detached = runGit(rootDir, 'rev-parse --short HEAD');
        branch = detached ? `DETACHED@${detached}` : 'DETACHED';
      }
    }
  }

  const languages: string[] = [];
  for (const [lang, markers] of LANGUAGE_MARKERS) {
    if (markers.some((m) => fs.existsSync(path.join(rootDir, m)))) {
      languages.push(lang);
    }
  }

  const test_surfaces: string[] = [];
  for (const testDir of ['tests', 'test', 'spec', '__tests__']) {
    if (fs.existsSync(path.join(rootDir, testDir)) && fs.statSync(path.join(rootDir, testDir)).isDirectory()) {
      test_surfaces.push(testDir);
    }
  }

  const executors: ExecutorStatus[] = KNOWN_EXECUTORS.map(([name, cmd]) => ({
    name,
    command: cmd,
    available: checkCommand(cmd),
  }));

  return {
    project_name: path.basename(rootDir),
    project_root: rootDir,
    git_available: gitAvailable,
    git_repository: gitRepo,
    branch,
    languages,
    test_surfaces,
    executors,
    timestamp: new Date().toISOString(),
  };
}
