pragma solidity ^0.6.2;

contract storage_vs_memory
{
    uint size;
    mapping(uint=>bool) my_mapping;

    constructor(uint _size) public {
        size = _size;
    }

    function with_storage() public returns(bool) {
        uint[] memory array_1;
        uint[] memory array_2;
        array_1 = new uint[](size);
        array_2 = new uint[](size);
        for (uint i = 0; i < size; i++) {
            array_1[i] = i;
            array_2[i] = i;
        }

        for (uint i = 0; i < array_2.length; i++) {
            my_mapping[array_2[i]] = true;
        }
        bool res = true;
        for (uint i = 0; i < array_1.length; i++) {
            if (my_mapping[array_1[i]] == false) {
                res = false;
            }
        }
        for (uint i = 0; i < array_2.length; i++) {
            my_mapping[array_2[i]] = false;
        }
        return res;
    }

    function with_memory() public view returns(bool) {
        uint[] memory array_1;
        uint[] memory array_2;
        array_1 = new uint[](size);
        array_2 = new uint[](size);
        for (uint i = 0; i < size; i++) {
            array_1[i] = i;
            array_2[i] = i;
        }

        bool res = true;
        for (uint i = 0; i < array_2.length; i++) {
            for (uint j = 0; j < array_1.length; j++) {
                if (array_1[i] != array_2[i]) {
                    res = false;
                }
            }
        }
        return res;
    }
}

