#!/usr/bin/env bash
source .env

node ../ethereum/scripts/create-bots.mjs "$ETH_URL" "$CONTRACT_ADDRESS" "$ACTIONS_FILE" "$INIT_BLOCK"