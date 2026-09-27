/**
 * Deterministic, conservative task characterization for P1.
 * Consumes explicit signals only.
 */

export enum Scope {
  SIMPLE = "SIMPLE",
  LOCALIZED = "LOCALIZED",
  REPOSITORY_WIDE = "REPOSITORY_WIDE",
  UNKNOWN = "UNKNOWN",
}

export enum RecommendedPath {
  SIMPLE_PATH = "SIMPLE_PATH",
  LOCALIZED_PATH = "LOCALIZED_PATH",
  REPOSITORY_WIDE_PATH = "REPOSITORY_WIDE_PATH",
  QUALIFICATION_REQUIRED = "QUALIFICATION_REQUIRED",
}

export enum Confidence {
  HIGH = "HIGH",
  MEDIUM = "MEDIUM",
  LOW = "LOW",
}

export interface TaskSignals {
  candidate_files?: string[] | null;
  dependency_edges?: Array<[string, string]> | null;
  affected_components?: string[] | null;
  known_tests?: string[] | null;
  ambiguity_markers?: string[] | null;
  risk_markers?: string[] | null;
  acceptance_checks?: string[] | null;
  state_shared?: boolean;
  architectural_change?: boolean;
}

export interface CharacterizationResult {
  scope: Scope;
  recommended_path: RecommendedPath;
  confidence: Confidence;
  reason_codes: string[];
  reasons: string[];
  characterized_at: string;
}

export function characterizeTask(signals: TaskSignals): CharacterizationResult {
  const reasons: string[] = [];
  const reason_codes: string[] = [];

  const candidateFiles = signals.candidate_files || [];
  const ambiguityMarkers = signals.ambiguity_markers || [];
  const riskMarkers = signals.risk_markers || [];
  const dependencyEdges = signals.dependency_edges || [];
  const affectedComponents = signals.affected_components || [];
  const knownTests = signals.known_tests || [];

  // Ambiguity check
  if (ambiguityMarkers.length > 0 || signals.candidate_files === null) {
    reason_codes.push("HIGH_AMBIGUITY");
    reasons.push(`Ambiguity markers detected: ${ambiguityMarkers.join(", ") || "missing candidate files"}`);
    return {
      scope: Scope.UNKNOWN,
      recommended_path: RecommendedPath.QUALIFICATION_REQUIRED,
      confidence: Confidence.LOW,
      reason_codes,
      reasons,
      characterized_at: new Date().toISOString(),
    };
  }

  // Repository wide check
  if (
    signals.architectural_change ||
    signals.state_shared ||
    candidateFiles.length > 5 ||
    affectedComponents.length > 2 ||
    dependencyEdges.length > 3
  ) {
    reason_codes.push("REPOSITORY_WIDE_SCOPE");
    if (signals.architectural_change) reasons.push("Explicit architectural change marked");
    if (signals.state_shared) reasons.push("Shared state mutation involved");
    if (candidateFiles.length > 5) reasons.push(`Broad candidate file count: ${candidateFiles.length}`);
    if (affectedComponents.length > 2) reasons.push(`Multiple affected components: ${affectedComponents.join(", ")}`);

    return {
      scope: Scope.REPOSITORY_WIDE,
      recommended_path: RecommendedPath.REPOSITORY_WIDE_PATH,
      confidence: knownTests.length > 0 ? Confidence.HIGH : Confidence.MEDIUM,
      reason_codes,
      reasons,
      characterized_at: new Date().toISOString(),
    };
  }

  // Localized check
  if (candidateFiles.length > 1 || dependencyEdges.length > 0 || riskMarkers.length > 0) {
    reason_codes.push("BOUNDED_LOCALIZED");
    reasons.push(`Bounded file set (${candidateFiles.length} files) across component(s): ${affectedComponents.join(", ")}`);
    if (riskMarkers.length > 0) {
      reasons.push(`Risk markers noted: ${riskMarkers.join(", ")}`);
    }

    return {
      scope: Scope.LOCALIZED,
      recommended_path: RecommendedPath.LOCALIZED_PATH,
      confidence: Confidence.HIGH,
      reason_codes,
      reasons,
      characterized_at: new Date().toISOString(),
    };
  }

  // Simple check
  reason_codes.push("SINGLE_FILE_OR_FOCUSED");
  reasons.push("Single file or tight focus with isolated component boundaries");

  return {
    scope: Scope.SIMPLE,
    recommended_path: RecommendedPath.SIMPLE_PATH,
    confidence: Confidence.HIGH,
    reason_codes,
    reasons,
    characterized_at: new Date().toISOString(),
  };
}
