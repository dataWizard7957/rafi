#!/usr/bin/env bash
# Import Rafi's tools and agents into watsonx Orchestrate (Tokyo instance).
# Prereqs: pip install --upgrade ibm-watsonx-orchestrate
#          orchestrate env add -n rafi -u <ORCHESTRATE_URL> --type ibm_iam   (verify flags in ADK docs)
#          orchestrate env activate rafi --api-key <ORCHESTRATE_APIKEY>
# Agents use the Orchestrate default model (gpt-oss-120b): llm: groq/openai/gpt-oss-120b.
# No Granite is available on our instance.
# VERIFY every command and flag below against the current ADK docs before running.
set -euo pipefail
cd "$(dirname "$0")"

: "${RAFI_API:?Set RAFI_API to your Cloud Run URL}"
: "${RAFI_KEY:?Set RAFI_KEY to the same value as the API}"

if ! grep -q "^llm:" agents/*.yaml; then
  echo "Every agents/*.yaml needs an llm: line (orchestrate models list)." >&2
  exit 1
fi

# 1. Connection holding the API URL and key for the tools
# add: -a flag is --app-id; ignore error if already exists
orchestrate connections add --app-id rafi_api || true
# configure: --kind key_value (not -k), --type team (member|team), --env draft
orchestrate connections configure --app-id rafi_api --env draft --kind key_value --type team
# set-credentials: key-value pairs use --entries (-e), not bare -e "KEY=VALUE"
orchestrate connections set-credentials --app-id rafi_api --env draft \
  --entries "RAFI_API=${RAFI_API}" --entries "RAFI_KEY=${RAFI_KEY}"

# 2. Tools (one file, all @tool functions)
# --requirements-file is the long form of -r
orchestrate tools import -k python -f tools/rafi_tools.py --requirements-file tools/requirements.txt --app-id rafi_api

# 3. Agents: collaborators first, Manager last
orchestrate agents import -f agents/shelf_agent.yaml
orchestrate agents import -f agents/review_agent.yaml
orchestrate agents import -f agents/rafi_manager.yaml

orchestrate agents list
