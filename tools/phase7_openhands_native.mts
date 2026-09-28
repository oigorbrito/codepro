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
  };
}

async function requestJson(args, method, path, body) {
  const response = await fetch(`${args.backendUrl}${path}`, {
    method,
    headers: {
      "X-Session-API-Key": args.apiKey,
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    signal: AbortSignal.timeout(30000),
  });
  const text = await response.text();
  if (!response.ok) throw new Error(`${method} ${path} -> ${response.status}: ${text.slice(0,1200)}`);
  return text ? JSON.parse(text) : null;
}

const TERMINAL = new Set(["finished","error","stuck"]);
async function pollConversation(args, conversationId) {
  const deadline = Date.now() + 240000;
  let info = null;
  const snapshots = [];
  while (Date.now() < deadline) {
    info = await requestJson(args, "GET", `/api/conversations/${encodeURIComponent(conversationId)}`);
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
  const joined = flattenStrings({ events, bashEvents }).map((x) => x.toLowerCase()).join("\n");
  return {
    commandObserved: joined.includes("terminal") || joined.includes("bashcommand") || joined.includes("bashoutput"),
    inspectObserved: joined.includes("value.py") && (joined.includes("cat ") || joined.includes("get-content") || joined.includes("read") || joined.includes("view") || joined.includes("python")),
    editObserved: joined.includes("file_editor") || joined.includes("str_replace") || joined.includes("write") || joined.includes("edit"),
  };
}

async function main() {
  const args = parseArgs();
  const result = {
    adapter: "openhands-agent-canvas-native",
    backend_url: args.backendUrl, working_dir: args.workingDir,
    llm_binding: { model: `openai/${args.modelAlias}`, base_url: args.llmBaseUrl, fallback: "DISABLED" },
    conversation_id: null, execution_status: null, final_reply: null,
    conversation_info: null, poll_snapshots: [], events: null, bash_events: null, observations: null, error: null,
  };
  try {
    setRegisteredBackends([{ id: "phase7-local", name: "Phase 7 Local", host: args.backendUrl, apiKey: args.apiKey, kind: "local" }]);
    setActiveSelection({ backendId: "phase7-local", orgId: null });
    const settings = {
      ...DEFAULT_SETTINGS,
      agent_settings: { ...DEFAULT_SETTINGS.agent_settings, llm: { model: `openai/${args.modelAlias}`, api_key: "local-llm", base_url: args.llmBaseUrl } },
      conversation_settings: { ...DEFAULT_SETTINGS.conversation_settings, max_iterations: 8 },
    };
    const payload = buildStartConversationRequest({ settings, query: args.issue, workingDir: args.workingDir, customSecrets: [] });
    const created = await requestJson(args, "POST", "/api/conversations", payload);
    const conversationId = String(created?.id ?? "");
    if (!conversationId) throw new Error(`conversation create returned no id: ${JSON.stringify(created)}`);
    result.conversation_id = conversationId;
    const polled = await pollConversation(args, conversationId);
    const info = polled.info;
    result.conversation_info = info;
    result.poll_snapshots = polled.snapshots;
    result.execution_status = info?.execution_status ?? null;
    try {
      const final = await requestJson(args, "GET", `/api/conversations/${encodeURIComponent(conversationId)}/agent_final_response`);
      result.final_reply = typeof final === "string" ? final : (final?.response ?? final?.content ?? JSON.stringify(final));
    } catch (error) { result.final_reply_error = error instanceof Error ? error.message : String(error); }
    const events = await requestJson(args, "GET", `/api/conversations/${encodeURIComponent(conversationId)}/events/search?limit=200&sort_order=TIMESTAMP_ASC`).catch((error) => ({ capture_error: error instanceof Error ? error.message : String(error) }));
    const bashEvents = await requestJson(args, "GET", "/api/bash/bash_events/search?limit=200").catch((error) => ({ capture_error: error instanceof Error ? error.message : String(error) }));
    result.events = events; result.bash_events = bashEvents; result.observations = deriveObservations(events, bashEvents);
    if (polled.timedOut) {
      result.error = { type: "Error", message: "conversation polling timed out after 240 seconds" };
    }
  } catch (error) {
    result.error = { type: error instanceof Error ? error.name : "Error", message: error instanceof Error ? error.message : String(error) };
  }
  await writeFile(args.result, `${JSON.stringify(result, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify(result)}\n`);
}

main().catch((error) => { process.stderr.write(`${error instanceof Error ? error.stack : String(error)}\n`); process.exitCode = 1; });
