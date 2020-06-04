pragma solidity ^0.6.2;


contract storage_vs_memory {
    uint256 size;

    uint256[] storageArray;

    constructor(uint256 _size) public {
        size = _size;
    }

    function with_storage() public {
        for (uint i = 0; i < size; i++) {
            storageArray.push(i);
        }
    }

    function with_memory() public view {
        uint256[] memory memoryArray = new uint256[](size);
        for (uint256 i = 0; i < size; i++) {
            memoryArray[i] = i;
        }
    }
}
