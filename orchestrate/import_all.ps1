# Import Rafi's tools and agents into watsonx Orchestrate (Tokyo instance).
#
# Tools are OpenAPI tools: Orchestrate calls the Rafi API /tools/* routes directly over HTTP.
# (Python tools failed on our instance with "Error getting Python tool status".)
#
# PREREQS
#   1. ADK connected and active:
#        .venv\Scripts\orchestrate env activate rafi-prod --api-key <ORCHESTRATE_APIKEY>
#   2. The Rafi API reachable at a public URL (Cloud Run, or a tunnel to localhost:8080).
#   3. In this shell:
#        $env:RAFI_API = "https://<public-api-url>"
#        $env:RAFI_KEY = "<same value as RAFI_KEY in .env>"
#        .\orchestrate\import_all.ps1
#
# Agents use the Orchestrate default model (llm: groq/openai/gpt-oss-120b in agents\*.yaml).
# Re-run this script whenever the public API URL changes. Afterwards, copy the printed
# rafi_manager ID into ORCHESTRATE_MANAGER_AGENT in .env (the runs API needs the ID, not the name).
#
# VERIFIED against ibm-watsonx-orchestrate 2.20.0 on 2026-11-14.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path $ScriptDir -Parent
$ORC = Join-Path $Root ".venv\Scripts\orchestrate.exe"
$PY = Join-Path $Root ".venv\Scripts\python.exe"
$Agents = @("shelf_agent", "review_agent", "rafi_manager")   # collaborators first, Manager last
$Tools = @("get_stock", "get_recent_orders", "create_task", "log", "scan_shelf", "get_settings", "mark_restocked",
           "get_new_reviews", "save_review_labels", "draft_reply", "get_open_tasks", "get_holds",
           "draft_supplier_order", "fulfill_holds", "notify_customer")

if (-not $env:RAFI_API) { Write-Error "Set `$env:RAFI_API to the public API URL first."; exit 1 }
if (-not $env:RAFI_KEY) { Write-Error "Set `$env:RAFI_KEY to the same value as RAFI_KEY in .env."; exit 1 }
foreach ($f in Get-ChildItem "$ScriptDir\agents\*.yaml") {
    if (-not (Select-String -Path $f.FullName -Pattern "^llm:" -Quiet)) { Write-Error "Add an llm: line to $($f.Name)"; exit 1 }
}

# Native commands write progress to stderr; don't treat that as a failure.
$ErrorActionPreference = "Continue"

Write-Host "`n--- Step 1: API-key connection (sends X-Rafi-Key) ---"
& $ORC connections add --app-id rafi_api_key
foreach ($e in "draft", "live") {
    & $ORC connections configure --app-id rafi_api_key --env $e --kind api_key --type team
    & $ORC connections set-credentials --app-id rafi_api_key --env $e --api-key $env:RAFI_KEY
}

Write-Host "`n--- Step 2: Build the OpenAPI spec for $env:RAFI_API ---"
& $PY "$ScriptDir\build_openapi.py" $env:RAFI_API "$ScriptDir\tools\rafi_openapi.json"
if ($LASTEXITCODE -ne 0) { Write-Error "Spec build failed"; exit 1 }

Write-Host "`n--- Step 3: Remove old agents and tools (ignore 'not found') ---"
foreach ($a in $Agents) { & $ORC agents remove -n $a -k native }
foreach ($t in $Tools) { & $ORC tools remove -n $t }

Write-Host "`n--- Step 4: Import OpenAPI tools ---"
& $ORC tools import -k openapi -f "$ScriptDir\tools\rafi_openapi.json" --app-id rafi_api_key

Write-Host "`n--- Step 5: Import agents ---"
foreach ($a in $Agents) { & $ORC agents import --file "$ScriptDir\agents\$a.yaml" }

Write-Host "`nDone. Set ORCHESTRATE_MANAGER_AGENT in .env to the rafi_manager 'Agent ID' printed above, then restart the API."
