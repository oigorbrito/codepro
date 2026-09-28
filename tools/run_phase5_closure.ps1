$ErrorActionPreference = "Stop"

$repoRoot = "D:\projetos\codepro-r2-validation"
$runtimeRoot = "D:\projetos\codepro-mini-runtime"
$branch = "phase5/local-runtime-plumbing"
$binRoot = "$runtimeRoot\downloads\llama-b11205-bin-win-cuda-13.4-x64"
$expectedBytes = 2244011552
$expectedSha = "E0406663965846AE22A403456EB826CCCE5F450840491F71952F18A7CB78E7D5"
$alias = "codepro-phase5-granite42-3b"
$port = 18088
$baseUrl = "http://127.0.0.1:$port/v1"
$evidenceRoot = "$repoRoot\evidence\phase5-local-runtime\frozen-smoke"
$clientEvidence = "$evidenceRoot\client"
$auditPath = "$repoRoot\docs\audits\phase5-local-runtime-plumbing-20260928.md"
$utf8 = [Text.UTF8Encoding]::new($false)
$nl = [Environment]::NewLine

Set-Location $repoRoot

Write-Host "======================================================"
Write-Host " PHASE 5 - LOCAL RUNTIME COMPLETE CLOSURE"
Write-Host "======================================================"

git fetch origin
if ($LASTEXITCODE -ne 0) { throw "git fetch failed." }
git switch $branch
if ($LASTEXITCODE -ne 0) { throw "git switch failed." }
git pull --ff-only origin $branch
if ($LASTEXITCODE -ne 0) { throw "git pull failed." }

$modelPath = $null
$candidates = @(Get-ChildItem "$runtimeRoot\models\phase4" -Filter "*.gguf" -File -Recurse | Where-Object { $_.Length -eq $expectedBytes })
foreach ($candidate in $candidates) {
    if ((Get-FileHash -Algorithm SHA256 $candidate.FullName).Hash -eq $expectedSha) {
        $modelPath = $candidate.FullName
        break
    }
}
if (-not $modelPath) { throw "Qualified L3 artifact not found by frozen SHA256." }

$server = Get-ChildItem $binRoot -Filter "llama-server.exe" -File -Recurse | Select-Object -First 1
if (-not $server) { throw "Frozen llama-server.exe not found." }

Write-Host "MODEL_PATH     = $modelPath"
Write-Host "MODEL_IDENTITY = PASS"
Write-Host "LLAMA_SERVER   = $($server.FullName)"

$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $port)
try { $listener.Start() } catch { throw "Explicit port $port unavailable." } finally { try { $listener.Stop() } catch {} }

$oldPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = "$repoRoot\src"
    & py -3.13 -m unittest -v tests.test_local_runtime
    if ($LASTEXITCODE -ne 0) { throw "Local-runtime unit tests failed." }
}
finally {
    $env:PYTHONPATH = $oldPythonPath
}
Write-Host "LOCAL_RUNTIME_UNIT_TESTS = PASS"

if (Test-Path $evidenceRoot) {
    $existingResultPath = "$clientEvidence\result.json"
    if (-not (Test-Path $existingResultPath)) {
        throw "Existing Phase 5 evidence has no result.json; refusing overwrite."
    }

    $existingResult = Get-Content $existingResultPath -Raw | ConvertFrom-Json
    $isKnownHarnessTruncation = (
        $existingResult.classification -eq "MODEL_RESPONSE_INVALID" -and
        $existingResult.telemetry.finish_reason -eq "length" -and
        $existingResult.telemetry.completion_tokens -eq 16
    )

    if (-not $isKnownHarnessTruncation) {
        throw "Existing Phase 5 evidence is not the known 16-token harness truncation; refusing overwrite."
    }

    $diagnosticsRoot = "$repoRoot\evidence\phase5-local-runtime\diagnostics"
    New-Item -ItemType Directory -Force -Path $diagnosticsRoot | Out-Null
    $archive = Join-Path $diagnosticsRoot "attempt-1-harness-truncated"
    if (Test-Path $archive) {
        throw "Diagnostic archive already exists: $archive"
    }

    Move-Item -LiteralPath $evidenceRoot -Destination $archive
    Write-Host "PREVIOUS_ATTEMPT_ARCHIVED = $archive"
}

New-Item -ItemType Directory -Force -Path $clientEvidence | Out-Null

$dq = [char]34
$serverArgs = @(
    "-m",
    "$dq$modelPath$dq",
    "--device",
    "CUDA0",
    "-ngl",
    "99",
    "-c",
    "4096",
    "--reasoning",
    "off",
    "--reasoning-budget",
    "0",
    "--host",
    "127.0.0.1",
    "--port",
    "$port",
    "--alias",
    $alias
) -join " "

$launch = [ordered]@{
    runtime = [ordered]@{ name = "llama.cpp"; build = 11205; commit = "95887577ab5fead779581a7030a83c7752ff3234"; executable = $server.FullName }
    model = [ordered]@{ phase4_candidate = "L3"; name = "Granite-4.2-3B"; artifact = $modelPath; bytes = $expectedBytes; sha256 = $expectedSha }
    binding = [ordered]@{ host = "127.0.0.1"; port = $port; base_url = $baseUrl; model_alias = $alias; fallback = "DISABLED" }
    argv = $serverArgs
}
[IO.File]::WriteAllText("$evidenceRoot\server-launch.json", (($launch | ConvertTo-Json -Depth 10) + $nl), $utf8)

$psi = New-Object Diagnostics.ProcessStartInfo
$psi.FileName = $server.FullName
$psi.Arguments = $serverArgs
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

$p = New-Object Diagnostics.Process
$p.StartInfo = $psi
$stdoutTask = $null
$stderrTask = $null
$started = $false
$ready = $false
$stopped = $false
$smoke = $null

try {
    $null = $p.Start()
    $started = $true
    $stdoutTask = $p.StandardOutput.ReadToEndAsync()
    $stderrTask = $p.StandardError.ReadToEndAsync()
    Write-Host "SERVER_START = PASS"

    for ($i = 0; $i -lt 180; $i++) {
        if ($p.HasExited) { break }
        try {
            $health = Invoke-RestMethod -Method Get -Uri "$baseUrl/health" -TimeoutSec 2
            if ($health.status -eq "ok") { $ready = $true; break }
        }
        catch {}
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { throw "llama-server did not become ready." }
    Write-Host "SERVER_HEALTH = PASS"

    $oldPythonPath = $env:PYTHONPATH
    try {
        $env:PYTHONPATH = "$repoRoot\src"
        $argsSmoke = @("tools/run_phase5_local_runtime_smoke.py", "--base-url", $baseUrl, "--model", $alias, "--timeout-seconds", "30", "--evidence-dir", $clientEvidence, "--expected", "PHASE5_OK")
        & py -3.13 @argsSmoke
        $smokeExit = $LASTEXITCODE
    }
    finally {
        $env:PYTHONPATH = $oldPythonPath
    }
    if ($smokeExit -ne 0) { throw "Real Phase 5 smoke failed." }

    $smoke = Get-Content "$clientEvidence\result.json" -Raw | ConvertFrom-Json
    if ($smoke.classification -ne "LOCAL_RUNTIME_PLUMBING_PASS") { throw "Unexpected smoke classification." }
    if ($smoke.response_valid -ne $true) { throw "Smoke response invalid." }
    if ($smoke.binding.model_id -ne $alias) { throw "Model binding changed." }
    if ($smoke.binding.fallback -ne "DISABLED") { throw "Fallback policy changed." }
    if ($smoke.telemetry.preflight.model_id -ne $alias) { throw "Preflight model mismatch." }

    Write-Host "E2E_SMOKE          = PASS"
    Write-Host "MODEL_BINDING      = PASS"
    Write-Host "NO_SILENT_FALLBACK = PASS"
}
finally {
    if ($started -and -not $p.HasExited) {
        try { $p.Kill(); $p.WaitForExit() } catch {}
    }
    if ($started) { try { $stopped = $p.HasExited } catch {} }
    $out = ""
    $err = ""
    if ($stdoutTask) { try { $out = $stdoutTask.Result } catch {} }
    if ($stderrTask) { try { $err = $stderrTask.Result } catch {} }
    [IO.File]::WriteAllText("$evidenceRoot\server-stdout.txt", $out, $utf8)
    [IO.File]::WriteAllText("$evidenceRoot\server-stderr.txt", $err, $utf8)
}

if (-not $stopped) { throw "llama-server remained running." }
if (-not $smoke) { throw "Smoke result missing." }
Write-Host "SERVER_STOP = PASS"

$summary = [ordered]@{
    schema_version = 1
    phase = 5
    status = "COMPLETE"
    path = "CodePro -> local inference server -> model -> response -> telemetry"
    runtime = [ordered]@{ name = "llama.cpp"; build = 11205; commit = "95887577ab5fead779581a7030a83c7752ff3234" }
    reference_fixture = [ordered]@{ candidate = "L3"; model = "Granite-4.2-3B"; role = "PHASE5_PLUMBING_FIXTURE"; selected_model = $false; sha256 = $expectedSha }
    binding = $smoke.binding
    smoke = [ordered]@{ classification = $smoke.classification; response_valid = $smoke.response_valid; expected_response = $smoke.expected_response; telemetry = $smoke.telemetry; provider_api_cost_usd = 0 }
    failure_boundaries = @("HTTP", "RUNTIME", "MODEL", "TIMEOUT", "PROTOCOL")
    gates = [ordered]@{ local_endpoint = "PASS"; endpoint_model_binding = "PASS"; no_silent_fallback = "PASS"; explicit_timeout = "PASS"; failure_separation = "PASS"; e2e_smoke = "PASS"; evidence_bundle = "PASS"; server_stop = "PASS" }
    next_phase = 6
}
[IO.File]::WriteAllText("$evidenceRoot\phase5-summary.json", (($summary | ConvertTo-Json -Depth 15) + $nl), $utf8)

New-Item -ItemType Directory -Force -Path (Split-Path $auditPath -Parent) | Out-Null
$auditLines = @(
    "# Phase 5 - CodePro local-runtime plumbing audit",
    "",
    "Date: 2026-09-28",
    "",
    "Frozen path: CodePro -> loopback llama-server -> exact model alias -> response -> telemetry.",
    "Reference fixture: L3 Granite 4.2 3B.",
    "REFERENCE_FIXTURE != SELECTED_MODEL",
    "COMPATIBLE != PROMOTED",
    "",
    "Endpoint: $baseUrl",
    "Model alias: $alias",
    "Timeout: 30 seconds",
    "Fallback: DISABLED",
    "Failure boundaries: HTTP, RUNTIME, MODEL, TIMEOUT, PROTOCOL.",
    "",
    "Smoke classification: $($smoke.classification)",
    "Response valid: $($smoke.response_valid)",
    "Wall time ms: $($smoke.telemetry.wall_time_ms)",
    "Prompt tokens: $($smoke.telemetry.prompt_tokens)",
    "Completion tokens: $($smoke.telemetry.completion_tokens)",
    "Total tokens: $($smoke.telemetry.total_tokens)",
    "Provider API cost USD: 0",
    "Server termination: PASS",
    "",
    "PHASE_5 = COMPLETE",
    "Evidence: evidence/phase5-local-runtime/frozen-smoke/",
    "Next: Phase 6 - execution and verifier plumbing."
)
[IO.File]::WriteAllLines($auditPath, $auditLines, $utf8)

$roadmapPath = "$repoRoot\roadmap.md"
$roadmap = [IO.File]::ReadAllText($roadmapPath)
$p5 = $roadmap.IndexOf("## Phase 5")
$p6 = $roadmap.IndexOf("## Phase 6")
if ($p5 -lt 0 -or $p6 -le $p5) { throw "Phase 5 roadmap boundaries missing." }
$prefix = $roadmap.Substring(0, $p5)
$phase5 = $roadmap.Substring($p5, $p6 - $p5)
$suffix = $roadmap.Substring($p6)
$phase5 = $phase5 -replace '(?m)^- \[ \] ', '- [x] '
$phase5 = [regex]::Replace($phase5, '\*\*Phase status:\*\* IN_PROGRESS[^\r\n]*', '**Evidence:** docs/audits/phase5-local-runtime-plumbing-20260928.md.' + $nl + $nl + '**Phase status:** COMPLETE')
$roadmap = $prefix + $phase5 + $suffix
$roadmap = $roadmap.Replace("PHASE 5   CodePro local plumbing        IN_PROGRESS", "PHASE 5   CodePro local plumbing        COMPLETE")
$roadmap = [regex]::Replace($roadmap, 'PHASE 5 = CODEPRO LOCAL-RUNTIME PLUMBING\r?\nSTATUS = IN_PROGRESS / REAL_SMOKE_PENDING', "PHASE 6 = EXECUTION AND VERIFIER PLUMBING" + $nl + "STATUS = NEXT")
[IO.File]::WriteAllText($roadmapPath, $roadmap, $utf8)

$readmePath = "$repoRoot\README.md"
$readme = [IO.File]::ReadAllText($readmePath)
$readme = $readme.Replace("CURRENT PHASE = PHASE 5 / CODEPRO LOCAL-RUNTIME PLUMBING", "CURRENT PHASE = PHASE 6 / EXECUTION AND VERIFIER PLUMBING")
if (-not $readme.Contains("### Phase 5 local-runtime closure")) {
    $anchor = "See [roadmap.md](roadmap.md)."
    if (-not $readme.Contains($anchor)) { throw "README anchor missing." }
    $section = @(
        "### Phase 5 local-runtime closure",
        "",
        "The explicit local-runtime path passed a real frozen-runtime smoke.",
        "CodePro -> loopback llama-server -> exact model alias -> response -> persisted telemetry/evidence.",
        "Fallback remains disabled and HTTP, runtime, model, timeout, and protocol failures remain distinct.",
        "Granite 4.2 3B is a Phase 5 plumbing fixture, not a selected or promoted product model.",
        "Evidence: docs/audits/phase5-local-runtime-plumbing-20260928.md.",
        ""
    ) -join $nl
    $readme = $readme.Replace($anchor, $section + $nl + $anchor)
}
[IO.File]::WriteAllText($readmePath, $readme, $utf8)

& py -3.13 tools/check_foundation.py
if ($LASTEXITCODE -ne 0) { throw "Foundation gate failed." }
Write-Host "FOUNDATION = PASS"

$oldPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = "$repoRoot\src"
    & py -3.13 -m unittest discover -s tests -t . -v
    if ($LASTEXITCODE -ne 0) { throw "Full Python suite failed." }
}
finally {
    $env:PYTHONPATH = $oldPythonPath
}
Write-Host "PYTHON_TESTS = PASS"

& npm run lint
if ($LASTEXITCODE -ne 0) { throw "npm lint failed." }
Write-Host "NPM_LINT = PASS"

& npm run build
if ($LASTEXITCODE -ne 0) { throw "npm build failed." }
Write-Host "NPM_BUILD = PASS"

$roadmapCheck = [IO.File]::ReadAllText($roadmapPath)
if (-not $roadmapCheck.Contains("PHASE 5   CodePro local plumbing        COMPLETE")) { throw "Roadmap Phase 5 not complete." }
if (-not $roadmapCheck.Contains("PHASE 6 = EXECUTION AND VERIFIER PLUMBING")) { throw "Roadmap Phase 6 pointer missing." }
Write-Host "ROADMAP_SYNC = PASS"

git add -- "README.md" "roadmap.md" "docs/audits/phase5-local-runtime-plumbing-20260928.md" "evidence/phase5-local-runtime"
if ($LASTEXITCODE -ne 0) { throw "git add failed." }

$staged = @(git diff --cached --name-only)
if ($staged.Count -eq 0) { throw "No Phase 5 closure files staged." }
if (@($staged | Where-Object { $_ -match '\.gguf$' }).Count -gt 0) { throw "GGUF unexpectedly staged." }

$headBefore = (git rev-parse HEAD).Trim()
git commit -m "phase5: close local runtime plumbing"
if ($LASTEXITCODE -ne 0) { throw "Closure commit failed." }
$headAfter = (git rev-parse HEAD).Trim()
if ($headAfter -eq $headBefore) { throw "HEAD did not advance." }

git push origin $branch
if ($LASTEXITCODE -ne 0) { throw "Push failed." }
git fetch origin
if ($LASTEXITCODE -ne 0) { throw "Post-push fetch failed." }

$remoteHead = (git rev-parse "origin/$branch").Trim()
if ($remoteHead -ne $headAfter) { throw "Remote HEAD mismatch." }
$ahead = [int]((git rev-list --count "origin/main..origin/$branch").Trim())
if ($ahead -lt 3) { throw "Expected implementation, runner, and closure commits." }

Write-Host ""
Write-Host "======================================================"
Write-Host " PHASE 5 - FINAL RESULT"
Write-Host "======================================================"
Write-Host "LOCAL_ENDPOINT       = PASS"
Write-Host "EXPLICIT_BINDING     = PASS"
Write-Host "NO_SILENT_FALLBACK   = PASS"
Write-Host "EXPLICIT_TIMEOUT     = PASS"
Write-Host "FAILURE_SEPARATION   = PASS"
Write-Host "E2E_SMOKE            = PASS"
Write-Host "EVIDENCE_BUNDLE      = PASS"
Write-Host "SERVER_STOP          = PASS"
Write-Host "FOUNDATION           = PASS"
Write-Host "PYTHON_TESTS         = PASS"
Write-Host "NPM_LINT             = PASS"
Write-Host "NPM_BUILD            = PASS"
Write-Host "PHASE5               = COMPLETE"
Write-Host "NEXT_PHASE           = PHASE6"
Write-Host "COMMIT_SHA           = $headAfter"
Write-Host "REMOTE_HEAD          = $remoteHead"
Write-Host "COMMITS_AHEAD_MAIN   = $ahead"
Write-Host "NEXT                 = REMOTE_PR_ACCEPTANCE_AND_MERGE"
