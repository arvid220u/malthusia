//Contract based on [https://docs.openzeppelin.com/contracts/3.x/erc721](https://docs.openzeppelin.com/contracts/3.x/erc721)
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract Malthusia is ERC721URIStorage {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    // Metadata contains everything that needs to be on-chain
    // Additional on-chain metadata includes: tokenURI, tokenId
    struct Metadata {
        address creator;
        uint256 robot_type;
        uint256 start_block;
    }

    mapping(uint256 => Metadata) _metadata;

    constructor() ERC721("Malthusia", "MLTH") {}

    function mintNFT(
        address recipient,
        string memory tokenURI,
        uint256 robot_type
    ) public returns (uint256) {
        _tokenIds.increment();

        uint256 newItemId = _tokenIds.current();
        _mint(recipient, newItemId);
        _setTokenURI(newItemId, tokenURI);
        uint256 start_block = _getStartBlock();
        _metadata[newItemId] = Metadata(recipient, robot_type, start_block);

        return newItemId;
    }

    // _getStartBlock returns a number corresponding to when the robot is supposed to start
    // This number will be translated by the game runner to a round, with the goal that when this contract
    // is called, the round that this start block is translated to is in the future.
    function _getStartBlock() private returns (uint256) {
        return block.number;
    }

    function creator(uint256 tokenId) public view returns (address) {
        require(
            _exists(tokenId),
            "Malthusia: Creator query for nonexistent token"
        );
        return _metadata[tokenId].creator;
    }
}
