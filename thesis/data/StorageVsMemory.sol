pragma solidity ^0.6.6;

contract StorageVsMemory {
    uint256 size;
    uint256[] storageArr;

    constructor(uint256 _size) public {
        size = _size;
    }

    function withStorage() public {
        for (uint i = 0; i < size; i++) {
            storageArr.push(i);
        }
    }

    function withMemory() public view {
        uint256[] memory memoryArr = new uint256[](size);
        for (uint256 i = 0; i < size; i++) {
            memoryArray[i] = i;
        }
    }
}
