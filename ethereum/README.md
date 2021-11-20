inspiration taken from the following tutorial: https://ethereum.org/en/developers/tutorials/how-to-write-and-deploy-an-nft/

each NFT will contain the following data:

- on-chain:
    - UID (just the token address)
    - creator (just the minter address)
    - robot type (on-chain because might have different costs / availabilities)
    - round (based on current datetime or something like that)
    - tokenURI (ipfs://CID link)
- off-chain direct metadata:
    - name (user-provided name, may be anything)
    - description (user-provided description, may be anything)
    - image (empty string "", or possibly a user-provided image)
    - code (ipfs://CID link)
- off-chain indirect code on ipfs:
    - the code in flattened format
