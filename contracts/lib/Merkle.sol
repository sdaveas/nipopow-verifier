// Created based on https://eprint.iacr.org/2016/452.pdf

pragma solidity ^0.6.0;

import "./Arrays.sol";
import "./Math.sol";


library Merkle {
    // Returns the ceiling of log2(number) ie the number number's digits
    function log2Ceiling(uint256 _number) public pure returns (uint256) {
        return math.log2Ceiling(_number);
    }

    // Returns 2^i so that number/2 < 2^i < number
    function closestPow2(uint256 number) public pure returns (uint256) {
        return math.closestPow2(number);
    }

    //  where A is hash(0|A) and AB is hash(1| hash( 0|A)| hash( 0|B))
    // At the end of all rounds hash is contained in position 0 of data
    function merkleTreeHash(bytes32[] memory data)
        public
        pure
        returns (bytes32)
    {
        // Hash all leafs
        for (uint256 i = 0; i < data.length; i++) {
            data[i] = sha256(abi.encodePacked(uint256(0), data[i]));
        }

        uint256 step = 2;
        while (step / 2 < data.length) {
            for (uint256 i = 0; i < data.length - step / 2; i += step) {
                data[i] = sha256(
                    abi.encodePacked(uint256(1), data[i], data[i + step / 2])
                );
            }
            step *= 2;
        }

        return data[0];
    }

    // Returns the merkle proof of node indicated by _index in data
    function path(bytes32[] memory data, uint256 _index)
        public
        pure
        returns (bytes32[] memory, bool[] memory)
    {
        uint256 index = _index;
        for (uint256 i = 0; i < data.length; i++) {
            data[i] = sha256(abi.encodePacked(uint256(0), data[i]));
        }

        uint256 proofIndex;
        uint256 proofLength = log2Ceiling(data.length);
        bytes32[] memory proof = new bytes32[](proofLength);
        bool[] memory siblings = new bool[](proofLength);

        uint256 step = 2;
        while (step / 2 < data.length) {
            for (uint256 i = 0; i < data.length - step / 2; i += step) {
                if (i == index) {
                    proof[proofIndex] = data[i + step / 2];
                    siblings[proofIndex] = true;
                    proofIndex++;
                    index = i;
                } else if (i + step / 2 == index) {
                    proof[proofIndex] = data[i];
                    siblings[proofIndex] = false;
                    proofIndex++;
                    index = i;
                }
                data[i] = sha256(
                    abi.encodePacked(uint256(1), data[i], data[i + step / 2])
                );
            }
            step *= 2;
        }

        // If the proof was smaller than log2(data.length), remove zero cells
        // proofIndex points the first zero record, or the end of the proof
        if (proofIndex != proof.length) {
            proof = arrays.subArrayBytes32(proof, 0, proofIndex);
            siblings = arrays.subArrayBool(siblings, 0, proofIndex);
        }

        return (proof, siblings);
    }

    // Returns the merkle tree root as calculated from a proof
    function rootFromPath(
        bytes32 nodeData,
        bytes32[] memory proof,
        bool[] memory siblings
    ) public pure returns (bytes32) {
        bytes32 h = sha256(abi.encodePacked(uint256(0), nodeData));
        bytes32 left;
        bytes32 right;

        for (uint256 i = 0; i < siblings.length; i++) {
            if (siblings[i] == true) {
                left = h;
                right = proof[i];
            } else {
                left = proof[i];
                right = h;
            }
            h = sha256(abi.encodePacked(uint256(1), left, right));
        }
        return h;
    }

    // Creates a consistancy proof for prefix _m of data.
    // The proof contains all intermediate nodes in order to reconstruct root
    // of data and root of data[:_m]
    function consProofSub(bytes32[] memory data, uint256 _m)
        public
        pure
        returns (bytes32[] memory)
    {
        uint256 start = 0;
        uint256 end = data.length;
        uint256 m = _m;
        uint256 k;

        // Max size of the proof is the height of the merkle tree
        bytes32[] memory proof = new bytes32[](log2Ceiling(data.length) + 1);
        uint256 proofIndex;

        while (m != end - start) {
            k = closestPow2(end - start);

            if (m <= k) {
                proof[proofIndex] = merkleTreeHash(
                    arrays.subArrayBytes32(data, start + k, end)
                );
                end = start + k;
            } else {
                proof[proofIndex] = merkleTreeHash(
                    arrays.subArrayBytes32(data, start, start + k)
                );
                start += k;
                m -= k;
            }
            proofIndex++;
            require(proofIndex < proof.length, "Proof too small");
        }

        proof[proofIndex++] = merkleTreeHash(
            arrays.subArrayBytes32(data, start, start + m)
        );

        // If the proof was smaller than its max size, strip zero elements
        // proofIndex points the first zero record, or the end of the proof
        if (proofIndex != proof.length) {
            proof = arrays.subArrayBytes32(proof, 0, proofIndex);
        }
        // Finally reverse the proof
        return arrays.reverse(proof);
    }

    // Returns the merkle root hash of the firsts n0 items of n1 data
    function root0FromConsProof(bytes32[] memory proof, uint256 n0, uint256 n1)
        public
        pure
        returns (bytes32)
    {
        require(n0 < n1, "n0 >= n1");
        uint256 k = closestPow2(n1);
        if (n0 < k) {
            return
                root0FromConsProof(
                    arrays.subArrayBytes32(proof, 0, proof.length - 1),
                    n0,
                    k
                );
        }
        if (n0 == k) {
            return proof[proof.length - 2];
        }
        bytes32 left = proof[proof.length - 1];
        bytes32 right = root0FromConsProof(
            arrays.subArrayBytes32(proof, 0, proof.length - 1),
            n0 - k,
            n1 - k
        );
        return sha256(abi.encodePacked(uint256(1), left, right));
    }

    // Returns the merkle root hash of n1 items. The proof was created with
    // prefix of size n0
    function root1FromConsProof(bytes32[] memory proof, uint256 n0, uint256 n1)
        public
        pure
        returns (bytes32)
    {
        if (proof.length == 2)
            return sha256(abi.encodePacked(uint256(1), proof[0], proof[1]));

        uint256 k = closestPow2(n1);
        bytes32 left;
        bytes32 right;

        if (n0 < k) {
            left = root1FromConsProof(
                arrays.subArrayBytes32(proof, 0, proof.length - 1),
                n0,
                k
            );
            right = proof[proof.length - 1];
        } else {
            left = proof[proof.length - 1];
            right = root1FromConsProof(
                arrays.subArrayBytes32(proof, 0, proof.length - 1),
                n0 - k,
                n1 - k
            );
        }
        return sha256(abi.encodePacked(uint256(1), left, right));
    }
}
