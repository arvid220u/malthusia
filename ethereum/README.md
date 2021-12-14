inspiration taken from the following tutorial: https://ethereum.org/en/developers/tutorials/how-to-write-and-deploy-an-nft/

each NFT will contain the following data:

- on-chain:
  - UID (just the token address)
  - creator (just the minter address)
  - robot type (on-chain because might have different costs / availabilities)
    - need to devise forwards-compatible scheme for this! maybe have robot type be integer that directly corresponds to the cost or something?
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