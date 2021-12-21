require("dotenv").config();
const fsp = require('fs').promises;
const { createAlchemyWeb3 } = require("@alch/alchemy-web3");

if (process.argv.length < 5) {
  console.log(`Usage: node create-bots.js eth_url contract_address actions_file\n\neth_url: web socket URL to a json-rpc node\ncontract_address: the address at which the Malthusia.sol contract is deployed\nactions_file: the path to the .jsonl file where actions should be written`)
  process.exit(9);
}

const eth_url = process.argv[2];
const contract_address = process.argv[3];
const actions_file = process.argv[4];
const INIT_BLOCK = 0;

function blockToRound(block) {
  // this should be a piece-wise linear function, I believe. remember to not change the past.
  return block - INIT_BLOCK;
}

// valueToRobotType maps a cost to a robot type
// we specify robot types using costs. this allows us to have fliexibility: for example, we might define
// a cost that is lower, but gives a probability over different robot types.
// invalid values lead to no robot...
// remember to not change the past.
function valueToRobotType(value) {
  if (value === (10**16).toString()) {
    return 0; // WANDERER
  }
  return -1; // NONE
}

async function main() {
  const web3 = createAlchemyWeb3(eth_url);

  const contract_source = require("../artifacts/contracts/Malthusia.sol/Malthusia.json");
  const contract = new web3.eth.Contract(contract_source.abi, contract_address);

  const options = {
    filter: {
    },
    fromBlock: 0
  };

  contract.events.Creation(options)
    .on('data', event => {
      console.log(`data: ${event}`);
      console.log(event);
      values = event.returnValues;
      robot_type = valueToRobotType(values.value);
      if (robot_type === -1) {
        console.log(`invalid value: ${values.value}. no robot created!`);
        return;
      }
      action = {
        type: "new_robot",
        round: blockToRound(values.start_block),
        code: values.code,
        robot_type: robot_type,
        creator: values.creator,
        uid: values.tokenId,
      };
      fsp.appendFile(actions_file, JSON.stringify(action) + "\n");
    })
    .on('changed', changed => {console.log(`changed: ${changed}`)})
    .on('error', err => {throw err})
    .on('connected', str => console.log(`connected: ${str}`))
}

main()

