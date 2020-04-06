// Wrapper for consistency.sol library

pragma solidity ^0.6.0;

import "./consistency.sol";


contract consistencyWrapper {
    // Returns the ceiling of log2(number) ie the number number's digits
    function log2Ceiling(uint256 _number) public pure returns (uint256) {
        return consistency.log2Ceiling(_number);
    }

    // Returns 2^i so that number/2 < 2^i < number
    function closestPow2(uint256 number) public pure returns (uint256) {
        return consistency.closestPow2(number);
    }

    //  where A is hash(0|A) and AB is hash(1| hash( 0|A)| hash( 0|B))
    // At the end of all rounds hash is contained in position 0 of data
    function merkleTreeHash(bytes32[] memory data)
        public
        pure
        returns (bytes32)
    {
        return consistency.merkleTreeHash(data);
    }

    // Returns the merkle proof of node indicated by _index in data
    function path(bytes32[] memory data, uint256 _index)
        public
        pure
        returns (bytes32[] memory, bool[] memory)
    {
        return consistency.path(data, _index);
    }

    // Returns the merkle tree root as calculated from a proof
    function rootFromPath(
        bytes32 nodeData,
        bytes32[] memory proof,
        bool[] memory siblings
    ) public pure returns (bytes32) {
        return consistency.rootFromPath(nodeData, proof, siblings);
    }

    // Creates a consistency proof for prefix _m of data.
    // The proof contains all intermediate nodes in order to reconstruct root
    // of data and root of data[:_m]
    function consProofSub(bytes32[] memory data, uint256 _m)
        public
        pure
        returns (bytes32[] memory)
    {
        return consistency.consProofSub(data, _m);
    }

    // Returns the merkle root hash of the firsts n0 items of n1 data
    function root0FromConsProof(bytes32[] memory proof, uint256 n0, uint256 n1)
        public
        pure
        returns (bytes32)
    {
        return consistency.root0FromConsProof(proof, n0, n1);
    }

    // Returns the merkle root hash of n1 items. The proof was created with
    // prefix of size n0
    function root1FromConsProof(bytes32[] memory proof, uint256 n0, uint256 n1)
        public
        pure
        returns (bytes32)
    {
        return consistency.root1FromConsProof(proof, n0, n1);
    }
}
