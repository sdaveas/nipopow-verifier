pragma solidity ^0.6.0;


// A tiny library for array manipulations
library Arrays {
    // Substitute for array[start:end] for bool[]
    function subArrayBool(bool[] memory array, uint256 start, uint256 end)
        public
        pure
        returns (bool[] memory)
    {
        require(end >= start, "Invalid limits");
        require(start < array.length, "Invalid limits");
        require(end <= array.length, "Invalid limits");
        bool[] memory subArray = new bool[](end - start);
        for (uint256 i = start; i < end; i++) {
            subArray[i - start] = array[i];
        }
        return subArray;
    }

    // Substitute for array[start:end] for bytes32[]
    function subArrayBytes32(bytes32[] memory array, uint256 start, uint256 end)
        public
        pure
        returns (bytes32[] memory)
    {
        require(end >= start, "b32 Invalid limits");
        require(start < array.length, "b32 Invalid limits");
        require(end <= array.length, "b32 Invalid limits");
        bytes32[] memory subArray = new bytes32[](end - start);
        for (uint256 i = start; i < end; i++) {
            subArray[i - start] = array[i];
        }
        return subArray;
    }

    // Substitute for array[::-1]
    function reverse(bytes32[] memory array)
        public
        pure
        returns (bytes32[] memory)
    {
        bytes32 tmp;
        for (uint256 i = 0; i < array.length / 2; i++) {
            tmp = array[i];
            array[i] = array[array.length - 1 - i];
            array[array.length - 1 - i] = tmp;
        }
        return array;
    }
}
