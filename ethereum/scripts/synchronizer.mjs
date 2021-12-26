import dotenv from "dotenv";
dotenv.config();
import { blockToRound } from "./common.mjs";
import { createAlchemyWeb3 } from "@alch/alchemy-web3";

if (process.argv.length < 4) {
  console.log(
    `Usage: node synchronizer.js eth_url init_block\n\neth_url: web socket URL to a json-rpc node\ninit_block: the eth block at which to start. can be past or present`
  );
  process.exit(9);
}

const eth_url = process.argv[2];
const init_block = process.argv[3];

// always stay 10 rounds behind, to ensure we don't walk into the future
const SAFETY_MARGIN = 10;

async function main() {
  const web3 = createAlchemyWeb3(eth_url);

  // the id of the last round the game completed (first round is round 1)
  let game_round = 0;

  const block_round = blockToRound(await web3.eth.getBlockNumber(), init_block);
  while (game_round < block_round - SAFETY_MARGIN) {
    console.log("");
    game_round++;
  }

  web3.eth
    .subscribe("newBlockHeaders")
    .on("data", (block) => {
      const block_round = blockToRound(block.number, init_block);
      while (game_round < block_round - SAFETY_MARGIN) {
        console.log("");
        game_round++;
      }
    })
    .on("error", (err) => {
      throw err;
    })
    .on("connected", (_) => {});
}

main();
