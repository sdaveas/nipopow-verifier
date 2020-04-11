// Created based on https://eprint.iacr.org/2016/452.pdf

pragma solidity ^0.6.0;

import "./Arrays.sol";
import "./Math.sol";


library Merkle {

    using Arrays for bytes32[];
    using Arrays for bool[];
    using Math for uint256;

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
        uint256 proofLength = data.length.log2Ceiling();
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
            proof = proof.subArrayBytes32(0, proofIndex);
            siblings = siblings.subArrayBool(0, proofIndex);
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

    // Inclusion verification for nodeData
    function verifyMerkleRoot(bytes32 root, bytes32 nodeData, bytes32[] memory proof, bool[] memory siblings)
        public
        pure
        returns(bool)
    {
        return root == rootFromPath(nodeData, proof, siblings);
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
        bytes32[] memory proof = new bytes32[](data.length.log2Ceiling() + 1);
        uint256 proofIndex;

        while (m != end - start) {
            k = (end - start).closestPow2();

            if (m <= k) {
                proof[proofIndex] = merkleTreeHash(
                    data.subArrayBytes32(start + k, end)
                );
                end = start + k;
            } else {
                proof[proofIndex] = merkleTreeHash(
                    data.subArrayBytes32(start, start + k)
                );
                start += k;
                m -= k;
            }
            proofIndex++;
            require(proofIndex < proof.length, "Proof too small");
        }

        proof[proofIndex++] = merkleTreeHash(
            data.subArrayBytes32(start, start + m)
        );

        // If the proof was smaller than its max size, strip zero elements
        // proofIndex points the first zero record, or the end of the proof
        if (proofIndex != proof.length) {
            proof = proof.subArrayBytes32(0, proofIndex);
        }
        // Finally reverse the proof
        return proof.reverse();
    }

    // Returns the merkle root hashes of overall and prefix data as
    // reconstructed from consistency proof
    function rootsFromConsistencyProof(bytes32[] memory proof, uint256 _first, uint256 _second)
        public
        pure
        returns (bytes32, bytes32)
    {
        require(_first > 0, "First <= 0");
        require(_second > _first, "Second <= First");

        bytes32 firstRoot= proof[0];
        bytes32 secondRoot = proof[0];
        uint256 first = _first - 1;
        uint256 second = _second - 1;

        while (first&1 == 1) {
            first >>=1;
            second >>=1;
        }

        for(uint256 i = 1; i < proof.length; i++) {
            if (second == 0) {
                return (bytes32(0), bytes32(0));
            }
            if (first&1 == 1 || first == second) {
                firstRoot = sha256(abi.encodePacked(uint256(1), proof[i], firstRoot));
                secondRoot = sha256(abi.encodePacked(uint256(1), proof[i], secondRoot));
                while (first&1 != 1 && first > 0) {
                    first >>= 1;
                    second >>= 1;
                }
            }
            else {
                secondRoot = sha256(abi.encodePacked(uint256(1), secondRoot, proof[i]));
            }
            first >>= 1;
            second >>= 1;
        }
        return (firstRoot, secondRoot);
    }

    // Consistecy proof verification
    function verifyConsistencyProof(
        bytes32[] memory proof,
        bytes32 firstRoot,
        uint256 firstSize,
        bytes32 secondRoot,
        uint256 secondSize
    ) public pure returns (bool)
    {
        bytes32 firstFromProof;
        bytes32 secondFromProof;
        (firstFromProof, secondFromProof) = rootsFromConsistencyProof(proof, firstSize, secondSize);
        return firstRoot == firstFromProof && secondRoot == secondFromProof;
    }

}
