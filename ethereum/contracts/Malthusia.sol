// SPDX-License-Identifier: MIT
pragma solidity ^0.8.9;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract Malthusia is ERC721URIStorage {
    /**
     * @dev Emitted when `tokenId` robot is created.
     */
    event Creation(
        uint256 indexed tokenId,
        uint256 value,
        uint256 start_block,
        string name,
        address creator,
        string code
    );

    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    constructor() ERC721("Malthusia", "MLTH") {}

    function createRobot(
        address recipient,
        string memory tokenURI,
        string calldata name,
        string calldata code
    ) public payable returns (uint256) {
        _tokenIds.increment();

        uint256 newItemId = _tokenIds.current();
        _mint(recipient, newItemId);
        _setTokenURI(newItemId, tokenURI);
        uint256 start_block = _getStartBlock();
        uint256 value = _getValue();

        emit Creation(newItemId, value, start_block, name, recipient, code);

        return newItemId;
    }

    // _getStartBlock returns a number corresponding to when the robot is supposed to start
    // This number will be translated by the game runner to a round, with the goal that when this contract
    // is called, the round that this start block is translated to is in the future.
    function _getStartBlock() private view returns (uint256) {
        return block.number;
    }

    // _getValue returns the value of the robot being created. It will map to a specific robot type
    // in a way specified by the game engine.
    function _getValue() private view returns (uint256) {
        return msg.value;
    }
}
