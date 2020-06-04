pragma solidity ^0.6.4;


//import "strings.sol";

contract Crosschain {
    event debug(string tag, uint256 value);

    //using strings for *;

    // TODO: Set the genesisBlock. Is it going to be constant?
    bytes32 genesisBlock;
    // Collateral to pay.
    uint256 constant z = 100000000000000000; // 0.1 eth

    // Nipopow proof.
    struct Nipopow {
        mapping(bytes32 => bool) curProofMap;
        mapping(uint256 => uint256) levelCounter;
        // Stores the block precedence in the proofs.
        // For example: Given proof [1, 2, 3] we have 3 -> 2, 2 -> 1.
        // Used for preventing filling the blockDAG with duplicates.
        mapping(bytes32 => mapping(bytes32 => bool)) blockPrecedence;
        // Stores DAG of blocks.
        mapping(bytes32 => bytes32[]) blockDAG;
        // Stores the hashes of the block headers of the best proof.

        mapping(bytes32 => bool) visitedBlock;
        bytes32[] traversalStack;
        bytes32[] ancestors;
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

    // pop() is not implemented in solidity.
    function stackPop(bytes32[] storage stack) internal {
        require(stack.length > 0);
        stack.pop();
    }

    function addProofToDag(Nipopow storage nipopow, bytes32[] memory proof)
        internal
    {
        for (uint256 i = 1; i < proof.length; i++) {
            if (!nipopow.blockPrecedence[proof[i - 1]][proof[i]]) {
                nipopow.blockPrecedence[proof[i - 1]][proof[i]] = true;
                nipopow.blockDAG[proof[i - 1]].push(proof[i]);
            }
        }
    }

    function findAncestors(Nipopow storage nipopow, bytes32 lastBlock)
        internal
    {
        nipopow.traversalStack.push(lastBlock);

        while (nipopow.traversalStack.length != 0) {
            bytes32 currentBlock = nipopow.traversalStack[nipopow
                .traversalStack
                .length - 1];

            nipopow.visitedBlock[currentBlock] = true;
            nipopow.ancestors.push(currentBlock);
            stackPop(nipopow.traversalStack);

            for (
                uint256 i = 0;
                i < nipopow.blockDAG[currentBlock].length;
                i++
            ) {
                if (!nipopow.visitedBlock[nipopow.blockDAG[currentBlock][i]]) {
                    nipopow.traversalStack.push(
                        nipopow.blockDAG[currentBlock][i]
                    );
                }
            }
        }
    }

    /*function ancestorsTraversal(Nipopow storage nipopow,
    bytes32 currentBlock, bytes32 blockOfInterest) internal returns(bool) {
    if (currentBlock == blockOfInterest) {
      return true;
    }
    // The graph is a DAG so we can do DFS without worrying about cycles.
    // We do keep a visited array because it is more expensive in terms of gas.
    // TODO: Depends on how expensive is the predicate evaluation which could
    // cost a lot of gas. Consider the gas trade-offs.
    bool predicateValue = false;
    for (uint i = 0; i < nipopow.blockDAG[currentBlock].length; i++) {
      predicateValue = ancestorsTraversal(nipopow,
        blockDAG[currentBlock][i],
        blockOfInterest) || predicateValue;
    }
    return predicateValue;
  }*/

    function predicate(Nipopow storage proof, bytes32 blockOfInterest)
        private
        returns (bool)
    {
        uint256 ancestorsGas = gasleft();
        bool Predicate = false;
        for (uint256 i = 0; i < proof.ancestors.length; i++) {
            if (proof.ancestors[i] == blockOfInterest) {
                Predicate = true;
            }
            // Clean the stored memory.
            proof.visitedBlock[proof.ancestors[i]] = false;
        }
        emit debug("predicate", ancestorsGas - gasleft());

        uint256 deleteGas = gasleft();
        delete proof.ancestors;
        emit debug("delete ancestors", deleteGas - gasleft());

        return Predicate;
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
                return uint8(i) - 1;
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
        uint256 lcaGas = gasleft();
        (proofLcaIndex, contestingLcaIndex) = getLca(nipopow, contestingProof);
        emit debug("lca", lcaGas - gasleft());
        uint256 bestArgsGas = gasleft();
        bool args = bestArg(nipopow, contestingProof, contestingLcaIndex) >
            bestArg(nipopow, nipopow.bestProof, proofLcaIndex);
        emit debug("best args", bestArgsGas - gasleft());
        return args;
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
        require(h == roothash);
    }

    // shift bits to the most segnificant byte (256-8 = 248)
    // and cast it to a 8-bit uint
    function b32ToUint8(bytes32 B) private pure returns (uint8) {
        return uint8(bytes1(B << 248));
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

            require(branchLength <= 5);
            require(merkleIndex <= 32);

            // Copy siblings.
            bytes32[] memory Siblings = new bytes32[](branchLength);
            for (uint8 j = 0; j < branchLength; j++)
                Siblings[j] = siblings[ptr + j];
            ptr += branchLength;

            // Verify the merkle tree proof
            verifyMerkle(
                headers[i - 1][0],
                hashedHeaders[i],
                merkleIndex,
                Siblings
            );
        }
    }

    function verify(
        Nipopow storage proof,
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory blockOfInterest
    ) internal returns (bool) {
        bytes32[] memory contestingProof = new bytes32[](headers.length);
        for (uint256 i = 0; i < headers.length; i++) {
            contestingProof[i] = hashHeader(headers[i]);
        }

        uint256 interlinkGas = gasleft();
        // Throws if invalid.
        validateInterlink(headers, contestingProof, siblings);
        emit debug("interlink:", interlinkGas - gasleft());

        if (compareProofs(proof, contestingProof)) {
            uint256 proofGas = gasleft();
            proof.bestProof = contestingProof;
            emit debug("proof <- proof:", proofGas - gasleft());
            // Only when we get the "best" we add them to the DAG.
            uint256 dagGas = gasleft();
            addProofToDag(proof, contestingProof);
            emit debug("dag", dagGas - gasleft());
        }

        uint256 ancestorsGas = gasleft();
        findAncestors(proof, proof.bestProof[0]);
        emit debug("ancestors", ancestorsGas - gasleft());

        bool p = predicate(proof, hashHeader(blockOfInterest));
        if (p) {
            emit debug("found:", 0);
        } else {
            emit debug("not found:", 0);
        }
        return p;
    }

    // TODO: Deleting a mapping is impossible without knowing
    // beforehand all the keys of the mapping. That costs gas
    // and it may be in our favor to never delete this stored memory.
    function submitEventProof(
        bytes32[4][] memory headers,
        bytes32[] memory siblings,
        bytes32[4] memory blockOfInterest
    ) public payable returns (bool) {
        uint256 _gas = gasleft();
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
            emit debug("Overall", _gas - gasleft());
            return true;
        }

        emit debug("Overall", _gas - gasleft());
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

        if (events[hashedBlock].expire < block.number) {
            return false;
        }

        uint256 _gas = gasleft();
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
            emit debug("Overall", _gas - gasleft());
            return true;
        }

        emit debug("Overall", _gas - gasleft());
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
