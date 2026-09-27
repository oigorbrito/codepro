/**
 * Bounded, rule-based routing and escalation policy for P3.
 */

import { CharacterizationResult, RecommendedPath, Scope } from "./characterization";
import { ProgressAssessmentResult, ProgressStatus } from "./progress";

export enum RoutingDecisionType {
  ROUTE = "ROUTE",
  REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION",
  REJECT_INVALID_INPUT = "REJECT_INVALID_INPUT",
}

export enum EscalationAction {
  CONTINUE = "CONTINUE",
  STOP_SUFFICIENT_EVIDENCE = "STOP_SUFFICIENT_EVIDENCE",
  ESCALATE = "ESCALATE",
  BLOCK = "BLOCK",
  REQUIRE_QUALIFICATION = "REQUIRE_QUALIFICATION",
}

export interface RoutingEvaluationRequest {
  characterization: CharacterizationResult;
  progress?: ProgressAssessmentResult;
  escalation_budget: number;
  current_escalation_level: number;
}

export interface RoutingEvaluationResult {
  decision: RoutingDecisionType;
  action: EscalationAction;
  selected_path: RecommendedPath;
  target_executor_tier: "LOCAL_FOCUSED" | "LOCAL_DEEP" | "GOVERNED_MULTI_FILE" | "BLOCKED";
  reasons: string[];
}

export function evaluateRouting(req: RoutingEvaluationRequest): RoutingEvaluationResult {
  const reasons: string[] = [];

  // Ambiguity / qualification required
  if (req.characterization.scope === Scope.UNKNOWN || req.characterization.recommended_path === RecommendedPath.QUALIFICATION_REQUIRED) {
    reasons.push("Task characterization reflects unknown scope or ambiguity markers; qualification required before binding");
    return {
      decision: RoutingDecisionType.REQUIRE_QUALIFICATION,
      action: EscalationAction.REQUIRE_QUALIFICATION,
      selected_path: RecommendedPath.QUALIFICATION_REQUIRED,
      target_executor_tier: "BLOCKED",
      reasons,
    };
  }

  // Stagnation or Blocked progress
  if (req.progress?.status === ProgressStatus.BLOCKED || req.progress?.status === ProgressStatus.STAGNATED) {
    if (req.current_escalation_level >= req.escalation_budget) {
      reasons.push(`Progress stalled and escalation budget (${req.escalation_budget}) exhausted`);
      return {
        decision: RoutingDecisionType.ROUTE,
        action: EscalationAction.BLOCK,
        selected_path: req.characterization.recommended_path,
        target_executor_tier: "BLOCKED",
        reasons,
      };
    }

    reasons.push(`Escalation triggered from level ${req.current_escalation_level} to ${req.current_escalation_level + 1}`);
    return {
      decision: RoutingDecisionType.ROUTE,
      action: EscalationAction.ESCALATE,
      selected_path: req.characterization.recommended_path,
      target_executor_tier: "GOVERNED_MULTI_FILE",
      reasons,
    };
  }

  // Normal routing
  if (req.characterization.scope === Scope.SIMPLE) {
    reasons.push("Simple single-file scope routed to fast local focused tier");
    return {
      decision: RoutingDecisionType.ROUTE,
      action: EscalationAction.CONTINUE,
      selected_path: RecommendedPath.SIMPLE_PATH,
      target_executor_tier: "LOCAL_FOCUSED",
      reasons,
    };
  }

  if (req.characterization.scope === Scope.LOCALIZED) {
    reasons.push("Localized multi-file scope routed to deep local analysis tier");
    return {
      decision: RoutingDecisionType.ROUTE,
      action: EscalationAction.CONTINUE,
      selected_path: RecommendedPath.LOCALIZED_PATH,
      target_executor_tier: "LOCAL_DEEP",
      reasons,
    };
  }

  reasons.push("Repository-wide scope routed to governed multi-file tier with explicit boundary verification");
  return {
    decision: RoutingDecisionType.ROUTE,
    action: EscalationAction.CONTINUE,
    selected_path: RecommendedPath.REPOSITORY_WIDE_PATH,
    target_executor_tier: "GOVERNED_MULTI_FILE",
    reasons,
  };
}
