/** Native OpenHands Agent Canvas / Agent Server Phase 7 S4 harness. */
import { writeFile } from "node:fs/promises";
import { setActiveSelection, setRegisteredBackends } from "#/api/backend-registry/active-store";
import { buildStartConversationRequest } from "#/api/agent-server-adapter";
import { DEFAULT_SETTINGS } from "#/services/settings";

function parseArgs() {
  const raw = process.argv.slice(2).filter((arg) => arg !== "--");
  const values = new Map();
  for (let i = 0; i < raw.length; i += 2) {
    const key = raw[i]; const value = raw[i + 1];
    if (!key?.startsWith("--") || value === undefined) throw new Error("invalid argument sequence");
    values.set(key.slice(2), value);
  }
  for (const key of ["backend-url","api-key","working-dir","llm-base-url","model-alias","result","issue"]) {
    if (!values.get(key)) throw new Error(`missing --${key}`);
  }
  return {
    backendUrl: values.get("backend-url"), apiKey: values.get("api-key"),
    workingDir: values.get("working-dir"), llmBaseUrl: values.get("llm-base-url"),
    modelAlias: values.get("model-alias"), result: values.get("result"), issue: values.get("issue"),
    completionLogDir: values.get("completion-log-dir") ?? null,
    pollTimeoutSeconds: Number(values.get("poll-timeout-seconds") ?? "240"),
    platformContract: values.get("platform-contract") ?? null,
    systemPromptProfile: values.get("system-prompt-profile") ?? null,
    conversationWorktree: values.get("conversation-worktree") ?? "true",
  };
}

function buildPlatformSystemSuffix(args) {
  if (args.platformContract === null) return null;
  const base = [
    "<PLATFORM_CONTRACT>",
    "Platform: Windows-native.",
    "Terminal tool shell: PowerShell. Use PowerShell syntax and cmdlets; do not use bash/GNU command syntax or POSIX redirection.",
    `Workspace: ${args.workingDir}`,
    "Use the Windows absolute workspace path exactly as reported by the tools. For file_editor, use Windows absolute paths (for example D:\\\\...); do not rewrite them as /tmp/... .",
  ];
  if (args.platformContract === "windows-powershell-v1") {
    return [...base, "</PLATFORM_CONTRACT>"].join("\\n");
  }
  if (args.platformContract === "windows-powershell-v2") {
    return [
      ...base,
      "Instruction precedence for this runtime: when generic OpenHands prompt or tool text conflicts with this contract, this Windows-native contract governs platform syntax and path shape.",
      "Generic examples mentioning find, grep, sed, cat -n, or absolute paths 'starting with /' are POSIX-only and are not valid instructions for this Windows-native cell.",
      "Use PowerShell-native equivalents such as Get-ChildItem and Get-Content. For file_editor, a drive-qualified path such as D:\\\\... is absolute; never convert it to a slash-rooted path.",
      "</PLATFORM_CONTRACT>",
    ].join("\\n");
  }
  throw new Error(`unsupported platform contract: ${args.platformContract}`);
}

function buildSystemPrompt(args) {
  if (args.systemPromptProfile === null) return null;
  if (args.systemPromptProfile !== "windows-minimal-v1") {
    throw new Error(`unsupported system prompt profile: ${args.systemPromptProfile}`);
  }
  return [
    "You are OpenHands agent, a coding assistant operating in the current repository.",
    "Use the provided tools to inspect the requested file, make the requested minimal edit, run the requested verification command, and finish only after verification succeeds.",
    "The platform contract in dynamic context is authoritative for shell syntax and path shape.",
    "Do not invent or rewrite the workspace path. Use the workspace path reported by the runtime.",
  ].join("\n");
}

async function requestJson(args, method, path, body, timeoutMs = 30000) {
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new Error("request timeout must be a positive finite number");
  }
  const response = await fetch(`${args.backendUrl}${path}`, {
    method,
    headers: {
      "X-Session-API-Key": args.apiKey,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    signal: AbortSignal.timeout(Math.max(1, Math.floor(timeoutMs))),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`${method} ${path} -> ${response.status}: ${text.slice(0,1200)}`);
  return text ? JSON.parse(text) : null;
}

const TERMINAL = new Set(["finished","error","stuck"]);
async function pollConversation(args, conversationId, deadline) {
  if (!Number.isFinite(deadline) || deadline <= Date.now()) {
    return { info: null, snapshots: [], timedOut: true };
  }
  let info = null;
  const snapshots = [];
  while (Date.now() < deadline) {
    const remainingMs = Math.max(1, deadline - Date.now());
    info = await requestJson(
      args,
      "GET",
      `/api/conversations/${encodeURIComponent(conversationId)}`,
      undefined,
      Math.min(30000, remainingMs),
    );
    snapshots.push({
      observed_at: new Date().toISOString(),
      execution_status: info?.execution_status ?? null,
      runtime_status: info?.runtime_info?.runtime_status ?? null,
      can_resume: info?.runtime_info?.can_resume ?? null,
      updated_at: info?.updated_at ?? null,
    });
    const status = String(info?.execution_status ?? "").toLowerCase();
    if (TERMINAL.has(status)) return { info, snapshots, timedOut: false };
    await new Promise((resolve) => setTimeout(resolve, 1500));
  }
  return { info, snapshots, timedOut: true };
}

function flattenStrings(value, out = []) {
  if (typeof value === "string") out.push(value);
  else if (Array.isArray(value)) for (const item of value) flattenStrings(item, out);
  else if (value && typeof value === "object") for (const item of Object.values(value)) flattenStrings(item, out);
  return out;
}

function deriveObservations(events, bashEvents) {
  const items = Array.isArray(events?.items) ? events.items : [];
  const actions = items.filter((event) => event?.kind === "ActionEvent");
  const terminalActions = actions.filter((event) => String(event?.tool_name ?? "").toLowerCase() === "terminal");
  const fileActions = actions.filter((event) => String(event?.tool_name ?? "").toLowerCase() === "file_editor");
  const terminalJoined = flattenStrings(terminalActions).map((x) => x.toLowerCase()).join("\n");
  const fileJoined = flattenStrings(fileActions).map((x) => x.toLowerCase()).join("\n");
  return {
    commandObserved: terminalActions.length > 0,
    inspectObserved:
      (fileActions.length > 0 && fileJoined.includes("view") && fileJoined.includes("value.py")) ||
      (terminalActions.length > 0 && terminalJoined.includes("value.py") && (terminalJoined.includes("get-content") || terminalJoined.includes("type ") || terminalJoined.includes("python"))),
    editObserved:
      fileActions.length > 0 &&
      (fileJoined.includes("str_replace") || fileJoined.includes("create") || fileJoined.includes("insert") || fileJoined.includes("write")),
  };
}

function materializeDirectAgentWithSystemPrompt(payload, systemPrompt) {
  const raw = payload;
  const agentSettings = raw?.agent_settings;
  if (!agentSettings || typeof agentSettings !== "object") {
    throw new Error("inline system prompt requires resolved agent_settings payload");
  }
  if (!agentSettings.llm || !Array.isArray(agentSettings.tools)) {
    throw new Error("resolved agent_settings is missing llm or tools");
  }

  const verification = agentSettings.verification ?? {};
  if (verification.critic_enabled === true) {
    throw new Error("direct-agent inline prompt transport does not support an enabled critic in this frozen cell");
  }

  const condenserSettings = agentSettings.condenser ?? {};
  let condenser = null;
  if (condenserSettings.enabled !== false) {
    const condenserLlm = {
      ...agentSettings.llm,
      stream: false,
      usage_id: "condenser",
    };
    condenser = {
      kind: "LLMSummarizingCondenser",
      llm: condenserLlm,
      max_size: condenserSettings.max_size ?? 240,
      keep_first: condenserSettings.keep_first ?? 2,
      minimum_progress: condenserSettings.minimum_progress ?? 0.1,
      hard_context_reset_max_retries: condenserSettings.hard_context_reset_max_retries ?? 5,
      hard_context_reset_context_scaling: condenserSettings.hard_context_reset_context_scaling ?? 0.8,
      ...(condenserSettings.max_tokens == null ? {} : { max_tokens: condenserSettings.max_tokens }),
    };
  }

  const includeDefaultTools = ["FinishTool", "ThinkTool"];
  if (agentSettings.enable_switch_llm_tool !== false) includeDefaultTools.push("SwitchLLMTool");

  const agent = {
    kind: "Agent",
    llm: agentSettings.llm,
    tools: agentSettings.tools,
    mcp_config: agentSettings.mcp_config ?? {},
    include_default_tools: includeDefaultTools,
    agent_context: agentSettings.agent_context ?? {},
    system_prompt: systemPrompt,
    condenser,
    critic: null,
    tool_concurrency_limit: agentSettings.tool_concurrency_limit ?? 1,
    ...(agentSettings.filter_tools_regex == null ? {} : { filter_tools_regex: agentSettings.filter_tools_regex }),
  };

  delete raw.agent_settings;
  raw.agent = agent;
  return raw;
}

async function main() {
  const args = parseArgs();
  const result = {
    adapter: "openhands-agent-canvas-native",
    backend_url: args.backendUrl, working_dir: args.workingDir,
    llm_binding: { model: `openai/${args.modelAlias}`, base_url: args.llmBaseUrl, fallback: "DISABLED" },
    conversation_id: null, execution_status: null, final_reply: null,
    conversation_info: null, poll_snapshots: [], events: null, bash_events: null, observations: null, error: null,
    platform_contract: args.platformContract,
    system_prompt_profile: args.systemPromptProfile,
    system_prompt_transport: null,
    conversation_worktree: args.conversationWorktree,
  };
  try {
    setRegisteredBackends([{ id: "phase7-local", name: "Phase 7 Local", host: args.backendUrl, apiKey: args.apiKey, kind: "local" }]);
    setActiveSelection({ backendId: "phase7-local", orgId: null });
    const platformSystemSuffix = buildPlatformSystemSuffix(args);
    const systemPrompt = buildSystemPrompt(args);
    const settings = {
      ...DEFAULT_SETTINGS,
      agent_settings: {
        ...DEFAULT_SETTINGS.agent_settings,
        ...(systemPrompt ? { system_prompt: systemPrompt } : {}),
        ...(platformSystemSuffix ? { agent_context: { ...(DEFAULT_SETTINGS.agent_settings?.agent_context ?? {}), system_message_suffix: platformSystemSuffix } } : {}),
        llm: { model: `openai/${args.modelAlias}`, api_key: "local-llm", base_url: args.llmBaseUrl, ...(args.completionLogDir ? { log_completions: true, log_completions_folder: args.completionLogDir } : {}) },
      },
      conversation_settings: { ...DEFAULT_SETTINGS.conversation_settings, max_iterations: 8 },
    };
    if (!["true", "false"].includes(args.conversationWorktree)) {
      throw new Error(`--conversation-worktree must be true or false, got ${args.conversationWorktree}`);
    }
    let payload = buildStartConversationRequest({
      settings,
      query: args.issue,
      workingDir: args.workingDir,
      worktree: args.conversationWorktree === "true",
      customSecrets: [],
    });
    if (systemPrompt) {
      payload = materializeDirectAgentWithSystemPrompt(payload, systemPrompt);
      result.system_prompt_transport = "start-conversation-direct-agent-v1";
    }
    if (!Number.isFinite(args.pollTimeoutSeconds) || args.pollTimeoutSeconds <= 0) {
      throw new Error("poll timeout must be a positive finite number");
    }
    const conversationDeadline = Date.now() + args.pollTimeoutSeconds * 1000;
    const created = await requestJson(
      args,
      "POST",
      "/api/conversations",
      payload,
      Math.max(1, conversationDeadline - Date.now()),
    );
    const conversationId = String(created?.id ?? "");
    if (!conversationId) throw new Error(`conversation create returned no id: ${JSON.stringify(created)}`);
    result.conversation_id = conversationId;
    const polled = await pollConversation(args, conversationId, conversationDeadline);
    const info = polled.info;
    result.conversation_info = info;
    result.poll_snapshots = polled.snapshots;
    result.execution_status = info?.execution_status ?? null;
    try {
      const final = await requestJson(args, "GET", `/api/conversations/${encodeURIComponent(conversationId)}/agent_final_response`);
      result.final_reply = typeof final === "string" ? final : (final?.response ?? final?.content ?? JSON.stringify(final));
    } catch (error) { result.final_reply_error = error instanceof Error ? error.message : String(error); }
    const events = await requestJson(args, "GET", `/api/conversations/${encodeURIComponent(conversationId)}/events/search?limit=100&sort_order=TIMESTAMP`).catch((error) => ({ capture_error: error instanceof Error ? error.message : String(error) }));
    const bashEvents = await requestJson(args, "GET", "/api/bash/bash_events/search?limit=100").catch((error) => ({ capture_error: error instanceof Error ? error.message : String(error) }));
    result.events = events; result.bash_events = bashEvents; result.observations = deriveObservations(events, bashEvents);
    if (polled.timedOut) {
      result.error = { type: "Error", message: `conversation polling timed out after ${args.pollTimeoutSeconds} seconds` };
    }
  } catch (error) {
    result.error = { type: error instanceof Error ? error.name : "Error", message: error instanceof Error ? error.message : String(error) };
  }
  await writeFile(args.result, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

main().catch((error) => { process.stderr.write(`${error instanceof Error ? error.stack : String(error)}\n`); process.exitCode = 1; });
