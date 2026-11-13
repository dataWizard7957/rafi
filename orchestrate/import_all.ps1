# Import Rafi's tools and agents into watsonx Orchestrate (Tokyo instance).
#
# PREREQS — run these once to connect the ADK to your Tokyo instance:
#
#   1. Add the environment (replace <URL> with your Tokyo service URL):
#      .venv\Scripts\orchestrate env add -n rafi -u <ORCHESTRATE_URL> --type ibm_iam
#
#   2. Activate it with your IBM IAM API key:
#      .venv\Scripts\orchestrate env activate rafi --api-key <ORCHESTRATE_APIKEY>
#
#   3. Agents use the Orchestrate default model (gpt-oss-120b), already set in
#      agents\*.yaml as llm: groq/openai/gpt-oss-120b. No Granite on our instance.
#      Check availability with: .venv\Scripts\orchestrate models list
#
#   4. (Optional) Fallback for rafi_manager: Claude Sonnet, if coordination is unreliable.
#
#   5. Set env vars in this shell, then run this script:
#      $env:RAFI_API = "https://<your-cloud-run-url>"   # must be deployed first
#      $env:RAFI_KEY = "<same value as in .env>"
#      .\orchestrate\import_all.ps1
#
# NOTE: RAFI_API must be the public Cloud Run URL.
#       Run `gcloud run deploy` first (see README.md step 5).
#
# VERIFIED against ibm-watsonx-orchestrate 2.20.0 on 2026-11-13.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve the script's own directory so paths work regardless of cwd
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Guard: required env vars ---
if (-not $env:RAFI_API) {
    Write-Error "Set `$env:RAFI_API to your Cloud Run URL before running this script."
    exit 1
}
if (-not $env:RAFI_KEY) {
    Write-Error "Set `$env:RAFI_KEY to the same value as RAFI_KEY in your .env."
    exit 1
}

# --- Guard: every agent YAML must declare an llm ---
$yamlFiles = Get-ChildItem "$ScriptDir\agents\*.yaml"
foreach ($f in $yamlFiles) {
    if (-not (Select-String -Path $f.FullName -Pattern "^llm:" -Quiet)) {
        Write-Error "Add an llm: line in $($f.Name) first. Run: .venv\Scripts\orchestrate models list"
        exit 1
    }
}

# Use the venv orchestrate CLI
$ORC = Join-Path (Split-Path $ScriptDir -Parent) ".venv\Scripts\orchestrate"

Write-Host "`n--- Step 1: Create key-value connection for Rafi API credentials ---"
# add: creates the connection slot (idempotent-ish; ignore error if it already exists)
& $ORC connections add --app-id rafi_api
# configure: declare this as a key-value connection, shared across the team
& $ORC connections configure --app-id rafi_api --env draft --kind key_value --type team
# set-credentials: store the actual values (never hard-coded in this file)
& $ORC connections set-credentials --app-id rafi_api --env draft `
    --entries "RAFI_API=$($env:RAFI_API)" `
    --entries "RAFI_KEY=$($env:RAFI_KEY)"

Write-Host "`n--- Step 2: Import Python tools ---"
& $ORC tools import `
    --kind python `
    --file "$ScriptDir\tools\rafi_tools.py" `
    --requirements-file "$ScriptDir\tools\requirements.txt" `
    --app-id rafi_api

Write-Host "`n--- Step 3: Import agents (collaborators first, Manager last) ---"
& $ORC agents import --file "$ScriptDir\agents\shelf_agent.yaml"
& $ORC agents import --file "$ScriptDir\agents\review_agent.yaml"
& $ORC agents import --file "$ScriptDir\agents\rafi_manager.yaml"

Write-Host "`n--- Imported agents ---"
& $ORC agents list

Write-Host "`nDone. All tools and agents imported into the active Orchestrate environment."
