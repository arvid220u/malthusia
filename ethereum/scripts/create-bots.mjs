import dotenv from "dotenv";
import path from "path";

dotenv.config();
import { blockToRound, valueToRobotType } from "./common.mjs";
import { promises as fsp } from "fs";
import { createAlchemyWeb3 } from "@alch/alchemy-web3";

import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

if (process.argv.length < 6) {
  console.log(
    `Usage: node create-bots.js eth_url contract_address actions_file init_block\n\neth_url: web socket URL to a json-rpc node\ncontract_address: the address at which the Malthusia.sol contract is deployed\nactions_file: the path to the .jsonl file where actions should be written\ninit_block: the eth block at which to start. past or present.`
  );
  process.exit(9);
}

const eth_url = process.argv[2];
const contract_address = process.argv[3];
const actions_file = process.argv[4];
const init_block = process.argv[5];

async function main() {
  const web3 = createAlchemyWeb3(eth_url);

  const source_raw = await fsp.readFile(
      path.join(__dirname, "../artifacts/contracts/Malthusia.sol/Malthusia.json")
  );
  const contract_source = JSON.parse(source_raw);

  const contract = new web3.eth.Contract(contract_source.abi, contract_address);

  const options = {
    filter: {},
    fromBlock: 0,
  };

  contract.events
    .Creation(options)
    .on("data", (event) => {
      console.log(`data: ${event}`);
      console.log(event);
      const values = event.returnValues;
      const robot_type = valueToRobotType(values.value);
      if (robot_type === -1) {
        console.log(`invalid value: ${values.value}. no robot created!`);
        return;
      }
      const action = {
        type: "new_robot",
        round: blockToRound(values.start_block, init_block),
        robot_type: robot_type,
        creator: values.creator,
        uid: values.tokenId,
        code: values.code,
      };
      fsp.appendFile(actions_file, JSON.stringify(action) + "\n");
    })
    .on("changed", (changed) => {
      console.log(`changed: ${changed}`);
    })
    .on("error", (err) => {
      throw err;
    })
    .on("connected", (str) => console.log(`connected: ${str}`));
}

main();
