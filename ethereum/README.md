inspiration taken from the following tutorial: https://ethereum.org/en/developers/tutorials/how-to-write-and-deploy-an-nft/

each NFT will contain the following data:

- on-chain:
  - UID (just the token ID)
  - creator (just the minter address)
  - robot type (on-chain because might have different costs / availabilities)
    - need to devise forwards-compatible scheme for this! maybe have robot type be integer that directly corresponds to the cost or something? oh interesting. yeah I like that idea. cannot update costs, sure, which is not GREAT but it is fine. oh wait I wanted some scheme where the costs are low in the beginning and then logistically grows (eventually settles on some level). maybe in usdc? nahhh.
  - round (based on current datetime or something like that)
  - tokenURI (ipfs://CID link)
- off-chain direct metadata:
  - name (user-provided name, may be anything)
  - description (user-provided description, may be anything)
  - image (empty string "", or possibly a user-provided image)
  - code (ipfs://CID link)
- off-chain indirect code on ipfs:
  - the code in flattened format

## instructions

1. create a `.env` file containing: 

```
API_URL="https://eth-ropsten.alchemyapi.io/v2/your-api-key"
PRIVATE_KEY="your-metamask-private-key"
```

(pls use a burner wallet)

2. Run `npx hardhat` to do various things

(note: there seems to be a problem with hardhat and node 17, do `export NODE_OPTIONS=--openssl-legacy-provider` to resolve)

3. In particular, always run `npx hardhat node` to start a new node. It will not persist state — so keep this running in the background.

4. Run `npx hardhat --network localhost run scripts/deploy.js` to deploy the contract.

5. Run `node scripts/mint-nft.js` to mint an NFT.

6. to mine empty block: run `npx hardhat --network localhost console` and then run `ethers.provider.send("evm_mine")`

## misc useful info

1. https://docs.openzeppelin.com/learn/deploying-and-interacting?pref=hardhat is a good guide

2. hardhat has two builtin networks: `hardhat` and `localhost`. the former is recreated and killed for every new process, whereas `localhost` is a single local instance. therefore, remember to specify `--network localhost` if you want to interact with `npx hardhat node`

3. https://ethereum.stackexchange.com/a/88122 tldr: non-view calls will not show return value if interacting from ethers. this is because in the real world you won't actually know the return value until it is mined. so in the real world to get the NFT id you would emit an event (ERC721 already does this, with the `Transfer` event). in ethers on a local network you can simulate an on-chain call using `callStatic`... except then it won't actually modify the contract I believe.

4. special solidity variables (e.g. `block`, `msg`): https://docs.soliditylang.org/en/v0.8.10/units-and-global-variables.html#special-variables-and-functions