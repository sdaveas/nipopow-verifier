pragma solidity ^0.6.4;

contract CompareStorage {

    bytes32[] best;

    function submitStorage(bytes32[] memory array)
    public
    returns (bool)
    {
        for(uint256 i; i<array.length; i++) {
            best.push(array[i]);
        }
        return true;
    }

    function contestStorage(bytes32[] memory array)
    public
    view
    returns (bool)
    {
        require(array.length >= best.length, "Contesting array is smaller");
        return (compareStorage(array));
    }

    function compareStorage(bytes32[] memory array)
    internal
    view
    returns (bool)
    {
        for(uint256 i; i < best.length; i++) {
            if (array[i] < best[i]) {
                return false;
            }
        }
        return true;
    }

    bytes32 hash;

    function submitMemory(bytes32[] memory array)
    public
    returns (bool)
    {
        hash = sha256(abi.encodePacked(array));
        return true;
    }

    function contestMemory(bytes32[] memory existingArray, bytes32[] memory newArray)
    public
    view
    returns (bool)
    {
        require(hash == sha256(abi.encodePacked(existingArray)), "Invalid existing array");
        require(newArray.length >= existingArray.length, "Contesting array is smaller");
        return (compareMemory(existingArray, newArray));
    }

    function compareMemory(bytes32[] memory array1, bytes32[] memory array2)
    internal
    pure
    returns (bool)
    {
        for(uint256 i; i < array1.length; i++) {
            if (array2[i] < array1[i]) {
                return false;
            }
        }
        return true;
    }
}
