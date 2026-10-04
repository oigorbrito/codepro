/**
 * CodePro ADR 0156, 0157, 0159, 0161 (PR40 Tranche):
 * - Localization Path Policy V2.1
 * - Outcome Evidence Guard
 * - Qualification Identity & Scope Invariant: NO_SILENT_SCOPE_EXPANSION
 */

export interface PathValidationResult {
  valid: boolean;
  normalized?: string;
  error?: string;
}

/**
 * Validates and normalizes repository-relative file paths according to ADR 0159 & 0161:
 * - Must be a concrete file, not a directory (no trailing slash or backslash)
 * - Must be repository-relative (no leading slash or backslash)
 * - Traversal components ('..') are strictly rejected
 * - Windows drive-relative or absolute paths ('C:foo', 'C:/foo', 'C:\\foo') are strictly rejected
 * - Non-drive colons ('foo:bar') are preserved
 * - Normalizes forward/backward slashes to canonical POSIX '/'
 * - Eliminates redundant current-dir './' prefixes
 */
export function validateRepositoryRelativePath(inputPath: string): PathValidationResult {
  if (typeof inputPath !== 'string') {
    return { valid: false, error: 'Path must be a string' };
  }

  const trimmed = inputPath.trim();
  if (trimmed.length === 0) {
    return { valid: false, error: 'Path must not be empty' };
  }

  // Reject Windows drive paths (e.g., C:foo, C:/foo, C:\foo)
  if (/^[A-Za-z]:/i.test(trimmed)) {
    return { valid: false, error: `Drive-relative/absolute paths are rejected: "${trimmed}"` };
  }

  // Reject absolute paths
  if (trimmed.startsWith('/') || trimmed.startsWith('\\')) {
    return { valid: false, error: `Absolute paths are rejected: "${trimmed}"` };
  }

  // Reject directory identifiers (trailing / or \)
  if (trimmed.endsWith('/') || trimmed.endsWith('\\')) {
    return { valid: false, error: `Trailing separators rejected (candidate must be a concrete file, not a directory): "${trimmed}"` };
  }

  // Normalize separators to POSIX
  const normalizedSeparators = trimmed.replace(/\\/g, '/');

  // Split into components and evaluate traversal
  const rawParts = normalizedSeparators.split('/');
  const cleanParts: string[] = [];

  for (const part of rawParts) {
    if (part === '' || part === '.') {
      continue; // Skip redundant empty or current-dir segments
    }
    if (part === '..') {
      return { valid: false, error: `Directory traversal components ('..') are rejected: "${trimmed}"` };
    }
    cleanParts.push(part);
  }

  if (cleanParts.length === 0) {
    return { valid: false, error: `Path resolves to empty after normalization: "${trimmed}"` };
  }

  const normalized = cleanParts.join('/');
  return { valid: true, normalized };
}

/**
 * Validates and deduplicates a list of candidate files.
 */
export function normalizeCandidateFiles(files: string[]): {
  valid: boolean;
  normalized: string[];
  failures: string[];
} {
  const normalizedSet = new Set<string>();
  const normalizedList: string[] = [];
  const failures: string[] = [];

  for (const f of files) {
    const res = validateRepositoryRelativePath(f);
    if (!res.valid) {
      failures.push(res.error || `Invalid path: "${f}"`);
    } else if (res.normalized && !normalizedSet.has(res.normalized)) {
      normalizedSet.add(res.normalized);
      normalizedList.push(res.normalized);
    }
  }

  return {
    valid: failures.length === 0,
    normalized: normalizedList,
    failures,
  };
}

/**
 * Checks NO_SILENT_SCOPE_EXPANSION:
 * Target files must be strictly within authorized scope.
 */
export function checkScopeInclusion(
  targetFiles: string[],
  authorizedScope: string[]
): {
  inScope: boolean;
  outOfScope: string[];
  normalizedTarget: string[];
  normalizedScope: string[];
} {
  const normScopeRes = normalizeCandidateFiles(authorizedScope);
  const normTargetRes = normalizeCandidateFiles(targetFiles);

  const scopeSet = new Set(normScopeRes.normalized);
  const outOfScope: string[] = [];

  for (const file of normTargetRes.normalized) {
    if (!scopeSet.has(file)) {
      outOfScope.push(file);
    }
  }

  return {
    inScope: outOfScope.length === 0 && normTargetRes.failures.length === 0,
    outOfScope,
    normalizedTarget: normTargetRes.normalized,
    normalizedScope: normScopeRes.normalized,
  };
}

/**
 * ADR 0157: Positive Outcome Evidence Guard
 * Verification and acceptance outcomes require a non-empty authority.
 * Positive states (PASS, ACCEPTED, VERIFIED) additionally require non-empty evidence references.
 */
export function validateOutcomeEvidence(
  status: 'VERIFIED' | 'PASS' | 'ACCEPTED' | 'FAILED' | 'BLOCKED' | 'REJECTED' | 'TIMED_OUT',
  authority: string,
  evidenceRef?: string | null
): { valid: boolean; failure?: string } {
  if (!authority || typeof authority !== 'string' || authority.trim().length === 0) {
    return {
      valid: false,
      failure: 'Outcome requires a non-empty authority attribution',
    };
  }

  const isPositive = status === 'VERIFIED' || status === 'PASS' || status === 'ACCEPTED';
  if (isPositive) {
    if (!evidenceRef || typeof evidenceRef !== 'string' || evidenceRef.trim().length === 0) {
      return {
        valid: false,
        failure: `Positive outcome "${status}" requires a non-empty evidence reference`,
      };
    }
  }

  return { valid: true };
}
