/**
 * Embedded experiment fixtures for CodePro chassis verification.
 */

import fs from 'fs';
import path from 'path';

export interface FixtureSummary {
  name: string;
  type: string;
  description: string;
  data: unknown;
}

export function loadFixtures(): Record<string, FixtureSummary> {
  const fixtures: Record<string, FixtureSummary> = {};
  const expDir = path.resolve('experiments');

  if (fs.existsSync(expDir)) {
    const files = fs.readdirSync(expDir);
    for (const file of files) {
      if (file.endsWith('.json')) {
        const fullPath = path.join(expDir, file);
        try {
          const content = JSON.parse(fs.readFileSync(fullPath, 'utf-8'));
          fixtures[file.replace('.json', '')] = {
            name: file,
            type: content.fixture_type || content.contract_type || 'EXPERIMENT_FIXTURE',
            description: content.description || 'CodePro test fixture',
            data: content,
          };
        } catch {
          // ignore unparseable
        }
      }
    }
  }

  return fixtures;
}
