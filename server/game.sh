#!/usr/bin/env bash
source .env

node ../ethereum/scripts/synchronizer.mjs "$ETH_URL" "$INIT_BLOCK" | \
../engine/bin/mlth.py run --action-file "$ACTIONS_FILE" --output-file "$REPLAY_FILE" --stdin-turn
