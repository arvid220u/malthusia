//Contract based on [https://docs.openzeppelin.com/contracts/3.x/erc721](https://docs.openzeppelin.com/contracts/3.x/erc721)
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract Malthusia is ERC721URIStorage {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    struct Metadata {
        address creator;
        uint256 robot_type;
        uint256 start_round;
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
        uint256 start_round = _getStartRound();
        _metadata[newItemId] = Metadata(recipient, robot_type, start_round);

        return newItemId;
    }

    function _getStartRound() private returns (uint256) {
        // TODO: make this use the current time, or something. is there a time oracle?
        return 0;
    }

    function creator(uint256 tokenId) public view returns (address) {
        require(
            _exists(tokenId),
            "Malthusia: Creator query for nonexistent token"
        );
        return _metadata[tokenId].creator;
    }
}
