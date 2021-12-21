require("dotenv").config();
const fs = require('fs');
const read = (path, type) => new Promise((resolve, reject) => {
  fs.readFile(path, type, (err, file) => {
    if (err) reject(err)
    resolve(file)
  })
})
const { createAlchemyWeb3 } = require("@alch/alchemy-web3");

if (process.argv.length < 6) {
  console.log(`Usage: node mint-nft.js eth_url contract_address robot_type name code_file\n\neth_url: web socket URL to a json-rpc node\ncontract_address: the address at which the Malthusia.sol contract is deployed`)
  process.exit(9);
}

const eth_url = process.argv[2];
const contract_address = process.argv[3];
const name = process.argv[4];
const code_file = process.argv[5];


async function mintNFT(tokenURI) {
  const PUBLIC_KEY = process.env.PUBLIC_KEY;
  const PRIVATE_KEY = process.env.PRIVATE_KEY;
  const web3 = createAlchemyWeb3(eth_url);
  const contract_source = require("../artifacts/contracts/Malthusia.sol/Malthusia.json");
  const contract = new web3.eth.Contract(contract_source.abi, contract_address);

  const nonce = await web3.eth.getTransactionCount(PUBLIC_KEY, "latest");

  const code = await read(code_file, "utf8")

  const tx = {
    from: PUBLIC_KEY,
    to: contract_address,
    nonce: nonce,
    gas: 500000,
    value: 10**16,
    data: contract.methods.createRobot(PUBLIC_KEY, tokenURI, name, code).encodeABI(),
  };

  const signPromise = web3.eth.accounts.signTransaction(tx, PRIVATE_KEY);
  signPromise
    .then((signedTx) => {
      web3.eth.sendSignedTransaction(
        signedTx.rawTransaction,
        function (err, hash) {
          if (!err) {
            console.log("The hash of your transaction is: ", hash);
          } else {
            console.log(
              "Something went wrong when submitting transaction: ",
              err
            );
          }
        }
      );
    })
    .catch((err) => {
      console.log("Promise failed: ", err);
    });
}

mintNFT("ipfs://QmPcud7RBxSxoypm8tU8Fidyv5y2V8rBLf8c3CF16NkJSs");
