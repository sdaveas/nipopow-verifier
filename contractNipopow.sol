pragma solidity ^0.6.2;


//import "strings.sol";

contract Crosschain {
    constructor(bytes32 genesis) public {
        genesisBlockHash = genesis;
    }

    // The genesis block hash
    bytes32 genesisBlockHash;
    // Collateral to pay.
    uint256 constant z = 100000000000000000; // 0.1 eth

    // Nipopow proof.
    struct Nipopow {
        mapping(bytes32 => bool) curProofMap;
        mapping(uint256 => uint256) levelCounter;
        bytes32[] bestProof;
    }

    struct Event {
        address payable author;
        uint256 expire;
        Nipopow proof;
    }

    // The key is the key value used for the predicate. In our case
    // the block header hash.
    mapping(bytes32 => Event) events;
    mapping(bytes32 => bool) finalizedEvents;

    // Security parameters.
    uint256 constant m = 15;
    uint256 constant k = 6; // Should be bigger.

    function memcpy(uint256 dest, uint256 src, uint256 len) private pure {
        // Copy word-length chunks while possible
        for (; len >= 32; len -= 32) {
            assembly {
                mstore(dest, mload(src))
            }
            dest += 32;
            src += 32;
        }
        // Copy remaining bytes.
        uint256 mask = 256**(32 - len) - 1;
        assembly {
            let srcpart := and(mload(src), not(mask))
            let destpart := and(mload(dest), mask)
            mstore(dest, or(destpart, srcpart))
        }
    }

    // Hash the header using double SHA256
    function hashHeader(bytes32[4] memory header)
        internal
        pure
        returns (bytes32)
    {
        // Compute the hash of 112-byte header.
        string memory s = new string(112);
        uint256 sptr;
        uint256 hptr;
        assembly {
            sptr := add(s, 32)
        }
        assembly {
            hptr := add(header, 0)
        }
        memcpy(sptr, hptr, 112);
        return sha256(abi.encodePacked(sha256(abi.encodePacked(s))));
    }

    function hashHeaders(bytes32[4][] memory headers)
        internal
        pure
        returns (bytes32[] memory)
    {
        bytes32[] memory hashedHeaders = new bytes32[](headers.length);
        for (uint256 i = 0; i < headers.length; i++) {
            hashedHeaders[i] = hashHeader(headers[i]);
        }
        return hashedHeaders;
    }

    function predicate(Nipopow storage proof, bytes32 blockOfInterest)
        internal
        view
        returns (bool)
    {
        for (uint256 i = 0; i < proof.bestProof.length; i++) {
            if (proof.bestProof[i] == blockOfInterest) {
                return true;
            }
        }
        return false;
    }

    function predicateMemory(bytes32[] memory proof, bytes32 blockOfInterest)
        internal
        pure
        returns (bool)
    {
        for (uint256 i = 0; i < proof.length; i++) {
            if (proof[i] == blockOfInterest) {
                return true;
            }
        }
        return false;
    }

    function getLca(Nipopow storage nipopow, bytes32[] memory cProof)
        internal
        returns (uint256, uint256)
    {
        for (uint256 i = 0; i < cProof.length; i++) {
            nipopow.curProofMap[cProof[i]] = true;
        }

        bytes32 lcaHash;

        uint256 bLca = 0;
        uint256 cLca = 0;
        for (uint256 i = 0; i < nipopow.bestProof.length; i++) {
            if (nipopow.curProofMap[nipopow.bestProof[i]]) {
                bLca = i;
                lcaHash = nipopow.bestProof[i];
                break;
            }
        }

        // Get the index of lca in the currentProof.
        for (uint256 i = 0; i < cProof.length; i++) {
            if (lcaHash == cProof[i]) {
                cLca = i;
                break;
            }
        }

        // Clear the map. We don't need it anymore.
        for (uint256 i = 0; i < cProof.length; i++) {
            nipopow.curProofMap[cProof[i]] = false;
        }

        return (bLca, cLca);
    }

    // TODO: Implement the O(log(maxLevel)) algorithm.
    function getLevel(bytes32 hashedHeader) internal pure returns (uint256) {
        uint256 hash = uint256(hashedHeader);

        for (uint256 i = 0; i <= 255; i++) {
            // Change endianess.
            uint256 pow = (i / 8) * 8 + 8 - (i % 8) - 1;
            uint256 mask = 2**pow;
            if ((hash & mask) != 0) {
                return uint8(i);
            }
        }
        return 0;
    }

    function bestArg(
        Nipopow storage nipopow,
        bytes32[] memory proof,
        uint256 alIndex
    ) internal returns (uint256) {
        uint256 maxLevel = 0;
        uint256 maxScore = 0;
        uint256 curLevel = 0;

        // Count the frequency of the levels.
        for (uint256 i = 0; i < alIndex; i++) {
            curLevel = getLevel(proof[i]);

            // Superblocks of level m are also superblocks of level m - 1.
            for (uint256 j = 0; j <= curLevel; j++) {
                nipopow.levelCounter[j]++;
            }

            if (maxLevel < curLevel) {
                maxLevel = curLevel;
            }
        }

        for (uint256 i = 0; i <= maxLevel; i++) {
            uint256 curScore = uint256(nipopow.levelCounter[i] * 2**i);
            if (nipopow.levelCounter[i] >= m && curScore > maxScore) {
                maxScore = nipopow.levelCounter[i] * 2**i;
            }
            // clear the map.
            nipopow.levelCounter[i] = 0;
        }

        return maxScore;
    }

    function compareProofs(
        Nipopow storage nipopow,
        bytes32[] memory contestingProof
    ) internal returns (bool) {
        if (nipopow.bestProof.length == 0) {
            return true;
        }
        uint256 proofLcaIndex;
        uint256 contestingLcaIndex;
        (proofLcaIndex, contestingLcaIndex) = getLca(nipopow, contestingProof);
        return
            bestArg(nipopow, contestingProof, contestingLcaIndex) >
            bestArg(nipopow, nipopow.bestProof, proofLcaIndex);
    }

    function verifyMerkle(
        bytes32 roothash,
        bytes32 leaf,
        uint8 mu,
        bytes32[] memory siblings
    ) internal pure {
        bytes32 h = leaf;
        for (uint256 i = 0; i < siblings.length; i++) {
            uint8 bit = mu & 0x1;
            if (bit == 1) {
                h = sha256(
                    abi.encodePacked(
                        sha256(
                            abi.encodePacked(
                                siblings[siblings.length - i - 1],
                                h
                            )
                        )
                    )
                );
            } else {
                h = sha256(
                    abi.encodePacked(
                        sha256(
                            abi.encodePacked(
                                h,
                                siblings[siblings.length - i - 1]
                            )
                        )
                    )
                );
            }
            mu >>= 1;
        }
        require(h == roothash, "Merkle verification failed");
    }

    // shift bits to the most segnificant byte (256-8 = 248)
    // and cast it to a 8-bit uint
    function b32ToUint8(bytes32 b) private pure returns (uint8) {
        return uint8(bytes1(b << 248));
    }

    function validateInterlink(
        bytes32[4][] memory headers,
        bytes32[] memory hashedHeaders,
        bytes32[] memory siblings
    ) internal pure {
        uint256 ptr = 0; // Index of the current sibling
        for (uint256 i = 1; i < headers.length; i++) {
            // hold the 3rd and 4th least significant bytes
            uint8 branchLength = b32ToUint8(
                (headers[i][3] >> 8) & bytes32(uint256(0xff))
            );
            uint8 merkleIndex = b32ToUint8(
                (headers[i][3] >> 0) & bytes32(uint256(0xff))
            );

            require(branchLength <= 5, "Branch length too big");
            require(merkleIndex <= 32, "Merkle index too big");

            // Copy siblings.
            bytes32[] memory reversedSiblings = new bytes32[](branchLength);
            for (uint8 j = 0; j < branchLength; j++)
                reversedSiblings[j] = siblings[ptr + j];
            ptr += branchLength;

            // Verify the merkle tree proof
            verifyMerkle(
                headers[i - 1][0],
                hashedHeaders[i],
                merkleIndex,
                reversedSiblings
            );
        }
    }

    // Genesis is the last element of headers at index headers[headers.length-1].
    function verifyGenesis(bytes32 genesis) internal view returns (bool) {
        return genesisBlockHash == genesis;
    }

    // If existingProof[exLca:] is subset of contestingProof[contLca:]
    // returns true, false otherwise
    function subsetProof(
        bytes32[] memory existing,
        uint256 existingLca,
        bytes32[] memory contesting,
        uint256 contestingLca
    ) internal pure returns (bool) {
        // If existing proof does not yet exists, return true
        if (existing.length == 0 && contesting.length != 0) {
            return true;
        }

        bool subset = true;
        uint256 j = contestingLca;

        for (
            uint256 i = existingLca;
            subset == true && i < existing.length;
            i++
        ) {
            while (existing[i] != contesting[j]) {
                j++;
                if (j >= contesting.length) {
                    subset = false;
                    break;
                }
            }
        }

        return subset;
    }

    // contestingProof -> contestingProofHashedHeaders
    // headers -> contesting proof headers
    function verify(
        Nipopow storage proof,
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory blockOfInterest
    ) internal returns (bool) {
        require(
            verifyGenesis(hashHeader(headers[headers.length - 1])),
            "Genesis"
        );

        bytes32[] memory contestingProof = new bytes32[](headers.length);
        for (uint256 i = 0; i < headers.length; i++) {
            contestingProof[i] = hashHeader(headers[i]);
        }

        // Throws if invalid.
        validateInterlink(headers, contestingProof, siblings);

        if (compareProofs(proof, contestingProof)) {
            uint256 existingLca;
            uint256 contestingLca;
            (existingLca, contestingLca) = getLca(proof, contestingProof);

            if (
                subsetProof(
                    proof.bestProof,
                    existingLca,
                    contestingProof,
                    contestingLca
                ) == false
            ) {
                return false;
            }
            // require(subsetProof(proof.bestProof, pLca, contestingProof, cLca), "Subset");

            proof.bestProof = contestingProof;
        } else {
            return true;
        }

        return predicate(proof, hashHeader(blockOfInterest));
    }

    // TODO: Deleting a mapping is impossible without knowing
    // beforehand all the keys of the mapping. That costs gas
    // and it may be in our favor to never delete this stored memory.
    function hashProof(bytes32[4][] memory headers)
        public
        payable
        returns (bytes32)
    {
        return sha256(abi.encodePacked(headers[0]));
    }

    function submitEventProof(
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory blockOfInterest
    ) public payable returns (bool) {
        bytes32 hashedBlock = hashHeader(blockOfInterest);

        if (msg.value < z) {
            return false;
        }

        // No proof for that event for the moment.
        if (
            events[hashedBlock].expire == 0 &&
            events[hashedBlock].proof.bestProof.length == 0 &&
            verify(
                events[hashedBlock].proof,
                headers,
                siblings,
                blockOfInterest
            )
        ) {
            events[hashedBlock].expire = block.number + k;
            events[hashedBlock].author = msg.sender;

            return true;
        }

        return false;
    }

    function finalizeEvent(bytes32[4] memory blockOfInterest)
        public
        returns (bool)
    {
        bytes32 hashedBlock = hashHeader(blockOfInterest);

        if (
            events[hashedBlock].expire == 0 ||
            block.number < events[hashedBlock].expire
        ) {
            return false;
        }
        finalizedEvents[hashedBlock] = true;
        events[hashedBlock].expire = 0;
        events[hashedBlock].author.transfer(z);

        return true;
    }

    function submitContestingProof(
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory blockOfInterest
    ) public returns (bool) {
        bytes32 hashedBlock = hashHeader(blockOfInterest);

        if (events[hashedBlock].expire <= block.number) {
            return false;
        }

        if (
            !verify(
                events[hashedBlock].proof,
                headers,
                siblings,
                blockOfInterest
            )
        ) {
            events[hashedBlock].expire = 0;
            msg.sender.transfer(z);
            return true;
        }

        return false;
    }

    function eventExists(bytes32[4] memory blockHeader)
        public
        view
        returns (bool)
    {
        bytes32 hashedBlock = hashHeader(blockHeader);
        return finalizedEvents[hashedBlock];
    }
}
